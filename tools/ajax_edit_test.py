import os
from datetime import datetime

from app import app, db, User, Budget


def run():
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        # Ensure test user exists
        email = 'ajax-smoke@test.local'
        user = User.query.filter_by(email=email).first()
        if not user:
            from werkzeug.security import generate_password_hash
            user = User(email=email, password=generate_password_hash('password123'), currency='USD')
            db.session.add(user)
            db.session.commit()
            print('Created test user', user.email)
        else:
            print('Using existing test user', user.email)

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        # Create a budget transaction to edit
        today = datetime.utcnow().date()
        # Use a category from the SelectField choices so edit validation is simpler
        create_data = {
            'category': 'Grocery',
            'amount': '12.34',
            'type': 'expense',
            'date': today.strftime('%Y-%m-%d')
        }
        res = client.post('/budgets/create', data=create_data, follow_redirects=False)
        # Find the created budget (most recent for this user)
        b = Budget.query.filter_by(user_id=user.id).order_by(Budget.id.desc()).first()
        if not b:
            print('Failed to create a budget transaction for the test')
            return
        print('Created budget id', b.id)

        # AJAX GET of edit form
        get_res = client.get(f'/budgets/edit/{b.id}?ajax=1', headers={'X-Requested-With': 'XMLHttpRequest'})
        print('AJAX GET status:', get_res.status_code)
        assert get_res.status_code == 200
        html = get_res.get_data(as_text=True)
        assert '<form' in html and 'ajax-edit-budget-form' in html
        print('AJAX GET returned edit form fragment')

        # AJAX POST to update the transaction
        new_amount = '99.99'
        post_data = {
            'category': b.category,
            'amount': new_amount,
            'type': b.type,
            'date': b.date.strftime('%Y-%m-%d') if b.date else today.strftime('%Y-%m-%d'),
            'next': '/budgets?from_date=&to_date=&page=1'
        }

        post_res = client.post(f'/budgets/edit/{b.id}?ajax=1', data=post_data, headers={'X-Requested-With': 'XMLHttpRequest'})
        print('AJAX POST status:', post_res.status_code)
        assert post_res.status_code == 200
        assert post_res.is_json
        j = post_res.get_json()
        print('AJAX POST response JSON:', j)
        assert j.get('success') is True

        # Verify DB updated
        db.session.expire_all()
        b2 = Budget.query.get(b.id)
        assert abs(float(b2.amount) - float(new_amount)) < 0.001
        print('DB updated: new amount =', b2.amount)

        print('\nAJAX edit test completed successfully.')


if __name__ == '__main__':
    run()
