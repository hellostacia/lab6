import hashlib
import os
import shutil
import uuid
from app import app
from models import db, Category, User, Image, Course

with app.app_context():
    db.create_all()

    category = db.session.execute(db.select(Category).filter_by(name='Программирование')).scalar()
    if category is None:
        category = Category(name='Программирование')
        db.session.add(category)

    user = db.session.execute(db.select(User).filter_by(login='user')).scalar()
    if user is None:
        user = User(first_name='Иван', last_name='Иванов', login='user')
        user.set_password('qwerty')
        db.session.add(user)

    db.session.commit()

    if db.session.execute(db.select(Course)).scalar() is None:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        source = os.path.join(app.root_path, 'static', 'images', 'polytech_logo.png')
        image_id = str(uuid.uuid4())
        destination = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.png')
        shutil.copy(source, destination)
        with open(source, 'rb') as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()
        image = Image(id=image_id, file_name='polytech_logo.png', mime_type='image/png', md5_hash=md5_hash)
        db.session.add(image)
        db.session.commit()

        course = Course(
            name='Основы Python',
            short_desc='Демонстрационный курс для проверки отзывов.',
            full_desc='На этом курсе можно проверить форму добавления отзывов, список последних отзывов и страницу всех отзывов с сортировкой.',
            category_id=category.id,
            author_id=user.id,
            background_image_id=image.id,
        )
        db.session.add(course)
        db.session.commit()

    print('Демо-данные созданы. Логин: user, пароль: qwerty')
