from flask_login import UserMixin
from datetime import datetime

def create_models(db):

    # -----------------------
    # USER MODEL
    # -----------------------
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(150), unique=True, nullable=False)
        password = db.Column(db.String(150), nullable=False)
        currency = db.Column(db.String(10), default='USD')

        tasks = db.relationship('Task', backref='user', lazy=True)
        budgets = db.relationship('Budget', backref='user', lazy=True)

    # -----------------------
    # TASK MODEL
    # -----------------------
    class Task(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text, nullable=True)
        deadline = db.Column(db.DateTime, nullable=False)
        priority = db.Column(db.String(10), default='Medium')
        status = db.Column(db.String(20), default='pending')
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

        def to_dict(self):
            """Return safe JSON-friendly task payload."""
            # ---- Convert deadline safely ----
            deadline_value = ""
            if self.deadline:
                if isinstance(self.deadline, str):
                    deadline_value = self.deadline
                else:
                    # This format works well for HTML datetime-local input
                    deadline_value = self.deadline.strftime("%Y-%m-%dT%H:%M")

            # ---- Calculate overdue + time left ----
            now = datetime.utcnow()
            is_overdue = False
            time_left = ""

            if self.deadline and not isinstance(self.deadline, str):
                if self.status == "done":
                    is_overdue = False
                elif self.deadline < now:
                    is_overdue = True
                    delta = now - self.deadline
                    total_sec = int(delta.total_seconds())
                    days = total_sec // 86400
                    hours = (total_sec % 86400) // 3600
                    minutes = (total_sec % 3600) // 60
                    time_left = f"Overdue by {days}d {hours}h {minutes}m"
                else:
                    delta = self.deadline - now
                    total_sec = int(delta.total_seconds())
                    days = total_sec // 86400
                    hours = (total_sec % 86400) // 3600
                    minutes = (total_sec % 3600) // 60
                    time_left = f"{days}d {hours}h {minutes}m left"

            return {
                "id": self.id,
                "title": self.title,
                "description": self.description or "",
                "deadline": deadline_value,
                "priority": self.priority or 'Medium',
                "tags": [t.name for t in getattr(self, 'tags_rel', [])],
                "status": self.status,
                "is_overdue": is_overdue,
                "time_left": time_left
            }

    # Association table for many-to-many Task <-> Tag
    task_tag = db.Table(
        'task_tag',
        db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    )

    class Tag(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), unique=True, nullable=False)

    # add relationship on Task dynamically to avoid name conflict
    Task.tags_rel = db.relationship('Tag', secondary=task_tag, backref=db.backref('tasks', lazy='dynamic'))

    # -----------------------
    # BUDGET MODEL
    # -----------------------
    class Budget(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        category = db.Column(db.String(100), nullable=False)
        amount = db.Column(db.Float, nullable=False)
        currency = db.Column(db.String(10), nullable=False, default='USD')
        type = db.Column(db.String(20), nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    return User, Task, Budget, Tag
