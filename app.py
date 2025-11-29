from flask import (
    Flask, render_template, redirect, url_for,
    flash, request, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from forms import LoginForm, RegisterForm, TaskForm, BudgetForm

from datetime import datetime, timedelta, timezone
from sqlalchemy import case, func, or_
import requests
import time
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook

# -------------------------------------------------
# Timezone: IST (UTC +5:30)
# -------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist_naive():
    """Return IST datetime (naive so it matches DB naive DateTime)."""
    return datetime.now(IST).replace(tzinfo=None)


# -------------------------------------------------
# Currency Helpers
# -------------------------------------------------
_rates_cache = {"ts": 0, "rates": {}, "base": None}


def get_conversion_rates(base="USD"):
    """Cached conversion rates for up to 10 minutes."""
    now = time.time()

    if _rates_cache.get("ts", 0) + 600 > now and _rates_cache.get("base") == base:
        return _rates_cache["rates"]

    try:
        res = requests.get(
            f"https://api.exchangerate.host/latest?base={base}",
            timeout=5
        )
        res.raise_for_status()
        data = res.json()
        rates = data.get("rates", {})
        _rates_cache.update({"ts": now, "rates": rates, "base": base})
        return rates
    except Exception:
        # fallback
        return {"USD": 1.0, "INR": 1.0}


def convert_amount(amount, from_cur, to_cur, rates):
    """Convert between currencies; fallback returns original amount."""
    try:
        if from_cur == to_cur:
            return float(amount)

        rf = rates.get(from_cur)
        rt = rates.get(to_cur)

        if rf and rt:
            amount_usd = float(amount) / float(rf)
            return amount_usd * float(rt)
    except Exception:
        pass

    return float(amount)


# -------------------------------------------------
# Flask App
# -------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

from models import create_models

User, Task, Budget, Tag = create_models(db)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


# Make `now_ist` available in templates if needed
@app.context_processor
def global_vars():
    return dict(now_ist=now_ist_naive)


# -------------------------------------------------
# HOME
# -------------------------------------------------
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)


# -------------------------------------------------
# REGISTER
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for("login"))

        user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            currency=form.currency.data,
        )

        db.session.add(user)
        db.session.commit()
        login_user(user)

        return redirect(url_for("dashboard"))

    return render_template("register.html", form=form)


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    # ---- TASK STATS ----
    tq = Task.query.filter_by(user_id=current_user.id)

    total_tasks = tq.count()
    completed = tq.filter(Task.status == "done").count()
    pending = tq.filter(Task.status == "pending").count()

    now = now_ist_naive()
    overdue = tq.filter(Task.deadline < now, Task.status != "done").count()

    next24 = now + timedelta(hours=24)
    due_soon = tq.filter(
        Task.status != "done",
        Task.deadline >= now,
        Task.deadline <= next24,
    ).order_by(Task.deadline.asc()).all()

    task_chart_data = {
        "labels": ["Pending", "Completed", "Overdue"],
        "values": [pending, completed, overdue],
    }

    # ---- BUDGET STATS ----
    bq = Budget.query.filter_by(user_id=current_user.id).all()

    user_cur = current_user.currency or "USD"
    rates = get_conversion_rates("USD")

    income = 0.0
    expense = 0.0

    for b in bq:
        conv = convert_amount(b.amount, b.currency, user_cur, rates)
        if b.type == "income":
            income += conv
        else:
            expense += conv

    finance_chart_data = {
        "labels": ["Income", "Expenses"],
        "values": [round(income, 2), round(expense, 2)],
    }

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue,
        due_soon=due_soon,
        total_income=income,
        total_expense=expense,
        balance=income - expense,
        currency=user_cur,
        task_chart_data=task_chart_data,
        finance_chart_data=finance_chart_data,
    )


# -------------------------------------------------
# TASKS
# -------------------------------------------------
@app.route("/tasks")
@login_required
def tasks():
    form = TaskForm()

    flt = request.args.get("filter", "all")
    sort = request.args.get("sort", "")
    priority_flt = request.args.get("priority", "")
    tag_search = request.args.get("tag", "").strip()

    q = Task.query.filter_by(user_id=current_user.id)

    now = now_ist_naive()

    if flt == "pending":
        q = q.filter(Task.status == "pending")
    elif flt == "done":
        q = q.filter(Task.status == "done")
    elif flt == "overdue":
        q = q.filter(Task.deadline < now, Task.status != "done")

    # Priority filter (if provided)
    if priority_flt:
        q = q.filter(Task.priority == priority_flt)

    # Tag filter (exact-token matching, require tasks to have ALL tokens)
    if tag_search:
        # support comma-separated tokens (require all tokens to match)
        tokens = [t.strip() for t in tag_search.split(',') if t.strip()]
        if tokens:
            # perform a join to tags, filter tag names to the token set (case-insensitive),
            # group by task and require the number of distinct matched tags >= number of tokens
            lower_tokens = [t.lower() for t in tokens]
            q = q.join(Task.tags_rel).filter(func.lower(Tag.name).in_(lower_tokens))
            q = q.group_by(Task.id).having(func.count(func.distinct(Tag.id)) >= len(tokens))

    # Sort rules: only two supported values
    if sort == "new":
        q = q.order_by(Task.deadline.desc())
    else:
        # default / 'old' -> oldest (asc)
        q = q.order_by(Task.deadline.asc())

    tasks_list = q.all()

    # Compute time-left / overdue
    for t in tasks_list:
        if not t.deadline:
            t.is_overdue = False
            t.time_left = ""
            continue

        if t.status == "done":
            t.is_overdue = False
            t.time_left = ""
        elif t.deadline < now:
            t.is_overdue = True
            delta = now - t.deadline
            sec = int(delta.total_seconds())
            t.time_left = f"Overdue by {sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
        else:
            t.is_overdue = False
            delta = t.deadline - now
            sec = int(delta.total_seconds())
            t.time_left = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m left"

        # Normalize tags for templates (use normalized relationship if available)
        try:
            t._tags_list = [tag.name for tag in getattr(t, 'tags_rel', [])]
        except Exception:
            t._tags_list = []

    return render_template("task_management.html", form=form, tasks=tasks_list, priority_filter=priority_flt, tag_search=tag_search)


# -------------------------------------------------
# TASK CREATE (AJAX)
# -------------------------------------------------
@app.route("/tasks/create", methods=["POST"])
@login_required
def create_task():
    form = TaskForm()

    if not form.validate_on_submit():
        flash("Please fix the errors in the task form.", "danger")
        return redirect(url_for("tasks"))

    dt = form.deadline.data
    if dt is None:
        flash("Deadline is required.", "danger")
        return redirect(url_for("tasks"))

    task = Task(
        title=form.title.data,
        description=form.description.data,
        deadline=dt,
        priority=form.priority.data,
        user_id=current_user.id,
    )

    db.session.add(task)
    # handle tags: parse, create/get Tag rows, associate
    tags_raw = (form.tags.data or '').strip()
    if tags_raw:
        names = [t.strip() for t in tags_raw.split(',') if t.strip()]
        for name in names:
            tag = Tag.query.filter(Tag.name.ilike(name)).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.flush()
            task.tags_rel.append(tag)

    db.session.commit()

    flash("Task created successfully.", "success")
    return redirect(url_for("tasks"))


    


# -------------------------------------------------
# TASK DELETE (AJAX)
# -------------------------------------------------
@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("tasks"))

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted.", "info")
    return redirect(url_for("tasks"))



# -------------------------------------------------
# TASK TOGGLE STATUS (AJAX)
# -------------------------------------------------
@app.route('/tasks/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("tasks"))

    task.status = "done" if task.status != "done" else "pending"
    db.session.commit()

    return redirect(url_for("tasks"))



# -------------------------------------------------
# EDIT TASK (normal request, not AJAX)
# -------------------------------------------------
@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash("Not authorized.", "danger")
        return redirect(url_for("tasks"))

    form = TaskForm()

    if form.validate_on_submit():
        dt = form.deadline.data
        if dt is None:
            flash("Invalid deadline.", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        task.title = form.title.data
        task.description = form.description.data
        task.deadline = dt
        task.priority = form.priority.data
        # update tags: clear existing and re-add
        task.tags_rel.clear()
        tags_raw = (form.tags.data or '').strip()
        if tags_raw:
            names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for name in names:
                tag = Tag.query.filter(Tag.name.ilike(name)).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                    db.session.flush()
                task.tags_rel.append(tag)

        db.session.commit()

        flash("Task updated.", "success")
        return redirect(url_for("tasks"))

    # Pre-fill form on GET
    if not form.is_submitted():
        form.title.data = task.title
        form.description.data = task.description
        form.deadline.data = task.deadline
        form.priority.data = task.priority
        # Pre-fill tags as comma-separated string
        existing_tags = ', '.join([tag.name for tag in task.tags_rel])
        form.tags.data = existing_tags

    return render_template("edit_task.html", form=form, task=task)


# -------------------------------------------------
# BUDGETS
# -------------------------------------------------
@app.route("/budgets")
@login_required
def budgets():
    form = BudgetForm()

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    q = Budget.query.filter_by(user_id=current_user.id)
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            q = q.filter(Budget.date >= from_dt)
        except Exception:
            pass
    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            q = q.filter(Budget.date <= to_dt)
        except Exception:
            pass


    transactions = q.order_by(Budget.date.desc()).all()

    user_cur = current_user.currency or "USD"
    rates = get_conversion_rates("USD")

    incomes = 0.0
    expenses = 0.0
    categories_all = {}
    categories_expenses = {}

    for t in transactions:
        conv = convert_amount(t.amount, t.currency, user_cur, rates)

        if t.type == "income":
            incomes += conv
        else:
            expenses += conv
            categories_expenses.setdefault(t.category, 0.0)
            categories_expenses[t.category] += conv

        categories_all.setdefault(t.category, 0.0)
        categories_all[t.category] += conv

    breakdown_all_list = list(categories_all.items())
    breakdown_expenses_list = list(categories_expenses.items())

    return render_template(
        "budget_management.html",
        form=form,
        transactions=transactions,
        incomes=incomes,
        expenses=expenses,
        balance=incomes - expenses,
        breakdown=breakdown_all_list,
        breakdown_expenses=breakdown_expenses_list,  # <- avoids Undefined in JS
        currency=user_cur,
    )


# -------------------------------------------------
# TAG SUGGESTIONS (AJAX)
# -------------------------------------------------
@app.route('/tags/suggest')
@login_required
def suggest_tags():
    q = request.args.get('q', '').strip()
    if q:
        tags = Tag.query.filter(Tag.name.ilike(f"{q}%")).order_by(Tag.name).limit(50).all()
    else:
        tags = Tag.query.order_by(Tag.name).limit(50).all()

    return jsonify([t.name for t in tags])


# -------------------------------------------------
# BUDGET CREATE
# -------------------------------------------------
@app.route("/budgets/create", methods=["POST"])
@login_required
def create_budget():
    form = BudgetForm()

    if not form.validate_on_submit():
        flash("Fix errors in the form.", "danger")
        return redirect(url_for("budgets"))

    # DateField → gives a date object
    if form.date.data:
        dt = datetime.combine(form.date.data, datetime.min.time())
    else:
        dt = now_ist_naive()

    selected_cat = form.category.data
    if selected_cat == "Other":
        custom = request.form.get("custom_category", "").strip()
        category_final = custom if custom else "Other"
    else:
        category_final = selected_cat

    b = Budget(
        category=category_final,
        amount=float(form.amount.data),
        currency=current_user.currency,
        type=form.type.data,
        date=dt,
        user_id=current_user.id,
    )

    db.session.add(b)
    db.session.commit()

    flash("Transaction added.", "success")
    return redirect(url_for("budgets"))


# -------------------------------------------------
# BUDGET DELETE
# -------------------------------------------------
@app.route("/budgets/delete/<int:bud_id>", methods=["POST"])
@login_required
def delete_budget(bud_id):
    b = Budget.query.get_or_404(bud_id)

    if b.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("budgets"))

    db.session.delete(b)
    db.session.commit()

    flash("Transaction deleted.", "info")
    return redirect(url_for("budgets"))


# -------------------------------------------------
# BUDGET EDIT
# -------------------------------------------------
@app.route("/budgets/edit/<int:bud_id>", methods=["GET", "POST"])
@login_required
def edit_budget(bud_id):
    b = Budget.query.get_or_404(bud_id)

    if b.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("budgets"))

    form = BudgetForm()

    if form.validate_on_submit():
        if form.date.data:
            dt = datetime.combine(form.date.data, datetime.min.time())
        else:
            dt = now_ist_naive()

        b.category = form.category.data
        b.amount = float(form.amount.data)
        b.type = form.type.data
        b.date = dt

        db.session.commit()

        flash("Transaction updated.", "success")
        return redirect(url_for("budgets"))

    if not form.is_submitted():
        form.category.data = b.category
        form.amount.data = b.amount
        form.type.data = b.type
        # Budget.date is DateTime → convert to date
        form.date.data = b.date.date() if b.date else None

    return render_template("edit_budget.html", form=form, bud=b)


# -------------------------------------------------
# EXPORT BUDGETS
# -------------------------------------------------
@app.route("/budgets/export")
@login_required
def export_budgets():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    fmt = request.args.get("format", "csv")

    q = Budget.query.filter_by(user_id=current_user.id)
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            q = q.filter(Budget.date >= from_dt)
        except Exception:
            pass

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            q = q.filter(Budget.date <= to_dt)
        except Exception:
            pass

    data = q.order_by(Budget.date.desc()).all()

    if fmt == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "Transactions"

        headers = ["ID", "Date", "Category", "Type", "Amount", "Currency"]
        ws.append(headers)

        for t in data:
            ws.append([
                t.id,
                t.date.strftime("%Y-%m-%d") if t.date else "",
                t.category,
                t.type,
                t.amount,
                t.currency,
            ])

        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)

        return (
            bio.read(),
            200,
            {
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Disposition": 'attachment; filename="transactions.xlsx"',
            },
        )

    # CSV
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Date", "Category", "Type", "Amount", "Currency"])
    for t in data:
        cw.writerow([
            t.id,
            t.date.strftime("%Y-%m-%d") if t.date else "",
            t.category,
            t.type,
            f"{t.amount:.2f}",
            t.currency,
        ])

    return (
        si.getvalue(),
        200,
        {
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; filename="transactions.csv"',
        },
    )


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
