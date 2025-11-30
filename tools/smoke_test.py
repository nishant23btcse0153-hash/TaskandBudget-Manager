import os
from datetime import datetime, timedelta

from app import app, db, User, Task, Tag


def run():
    app.config['WTF_CSRF_ENABLED'] = False``

    with app.app_context():
        # create or get test user
        email = 'smoke@test.local'
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, password='smoke-pass', currency='USD')
            # store a dummy hashed password
            from werkzeug.security import generate_password_hash
            user.password = generate_password_hash('password123')
            db.session.add(user)
            db.session.commit()
            print('Created test user', user.email)
        else:
            print('Using existing test user', user.email)

        client = app.test_client()

        # Log in by setting session directly
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        # Create tasks with tags
        now = datetime.utcnow()
        deadlines = [now + timedelta(days=2), now + timedelta(days=3), now + timedelta(days=1, hours=5)]
        payloads = [
            {'title': 'Task One', 'description': 'First', 'deadline': deadlines[0].strftime('%Y-%m-%dT%H:%M'), 'priority': 'High', 'tags': 'one,two'},
            {'title': 'Task Two', 'description': 'Second', 'deadline': deadlines[1].strftime('%Y-%m-%dT%H:%M'), 'priority': 'Medium', 'tags': 'two,three'},
            {'title': 'Task Three', 'description': 'Third', 'deadline': deadlines[2].strftime('%Y-%m-%dT%H:%M'), 'priority': 'Low', 'tags': 'one,three'},
        ]

        created_ids = []
        for p in payloads:
            res = client.post('/tasks/create', data=p, follow_redirects=False)
            # After creation, tasks page redirects. We'll fetch list to find created tasks
        # Query DB for created tasks
        ts = Task.query.filter_by(user_id=user.id).all()
        print('\nTasks in DB:')
        for t in ts:
            print(f"- {t.id}: {t.title} tags={[tag.name for tag in t.tags_rel]}")
            created_ids.append(t.id)

        # Test tag AND filtering: tag=one,two should return only tasks that have BOTH 'one' and 'two'
        res = client.get('/tasks?tag=one,two')
        assert res.status_code == 200
        body = res.get_data(as_text=True)
        found = body.count('task-card')
        print('\nFilter tag=one,two -> number of task cards in HTML:', found)
        # Also check that Task One (tags one,two) is present and Task Three (one,three) is not
        has_task_one = 'Task One' in body
        has_task_three = 'Task Three' in body
        print('Has Task One:', has_task_one)
        print('Has Task Three:', has_task_three)

        # Now check redirect preservation on toggle: pick one task id and toggle
        sample_id = ts[0].id
        toggle_res = client.post(f'/tasks/toggle/{sample_id}', data={'next': '/tasks?tag=one,two'}, follow_redirects=False)
        loc = toggle_res.headers.get('Location')
        print('\nToggle redirect Location header:', loc)

        # Edit redirect preservation: GET edit with next, then POST update and ensure redirect
        edit_get = client.get(f'/tasks/edit/{sample_id}?next=/tasks?tag=one,two')
        assert edit_get.status_code == 200
        # Post an update (change title)
        post_data = {
            'title': 'Task One Edited',
            'description': 'First edited',
            'deadline': deadlines[0].strftime('%Y-%m-%dT%H:%M'),
            'priority': 'High',
            'tags': 'one,two',
            'next': '/tasks?tag=one,two'
        }
        edit_post = client.post(f'/tasks/edit/{sample_id}', data=post_data, follow_redirects=False)
        print('Edit POST redirect Location:', edit_post.headers.get('Location'))

        print('\nSmoke test completed.')


if __name__ == '__main__':
    run()
