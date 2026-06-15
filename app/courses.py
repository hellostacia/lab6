from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

REVIEW_SORTS = {
    'new': Review.created_at.desc(),
    'positive': Review.rating.desc(),
    'negative': Review.rating.asc(),
}


def params():
    return {p: request.form.get(p) or None for p in COURSE_PARAMS}


def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }


def current_user_review(course_id):
    if not current_user.is_authenticated:
        return None
    return db.session.execute(
        db.select(Review).filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar()


@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())


@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)


@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                               categories=categories,
                               users=users,
                               course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')
    return redirect(url_for('courses.index'))


@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)
    latest_reviews = db.session.execute(
        db.select(Review)
        .filter_by(course_id=course.id)
        .order_by(Review.created_at.desc())
        .limit(5)
    ).scalars()
    user_review = current_user_review(course.id)
    return render_template('courses/show.html', course=course,
                           latest_reviews=latest_reviews,
                           user_review=user_review)


@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = db.get_or_404(Course, course_id)
    sort = request.args.get('sort', 'new')
    order = REVIEW_SORTS.get(sort, REVIEW_SORTS['new'])
    query = db.select(Review).filter_by(course_id=course.id).order_by(order, Review.created_at.desc())
    pagination = db.paginate(query, page=request.args.get('page', 1, type=int), per_page=5, error_out=False)
    user_review = current_user_review(course.id)
    return render_template('courses/reviews.html', course=course,
                           reviews=pagination.items,
                           pagination=pagination,
                           sort=sort,
                           user_review=user_review)


@bp.route('/<int:course_id>/reviews/create', methods=['POST'])
@login_required
def create_review(course_id):
    course = db.get_or_404(Course, course_id)
    if current_user_review(course.id):
        flash('Вы уже оставили отзыв к этому курсу.', 'warning')
        return redirect(request.referrer or url_for('courses.show', course_id=course.id))

    try:
        rating = int(request.form.get('rating', 5))
    except ValueError:
        rating = -1
    text = request.form.get('text', '').strip()

    if rating < 0 or rating > 5:
        flash('Оценка должна быть числом от 0 до 5.', 'danger')
        return redirect(request.referrer or url_for('courses.show', course_id=course.id))
    if not text:
        flash('Текст отзыва не может быть пустым.', 'danger')
        return redirect(request.referrer or url_for('courses.show', course_id=course.id))

    review = Review(rating=rating, text=text, course=course, user=current_user)
    course.rating_sum = (course.rating_sum or 0) + rating
    course.rating_num = (course.rating_num or 0) + 1
    db.session.add(review)
    db.session.commit()
    flash('Отзыв успешно добавлен.', 'success')
    return redirect(request.referrer or url_for('courses.show', course_id=course.id))
