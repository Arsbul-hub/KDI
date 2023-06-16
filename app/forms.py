import re
from datetime import datetime

from flask import session
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, URLField, TelField, EmailField, \
    SelectField
from wtforms.widgets import TextArea
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Config, Gallery
from app import app
from app.validators import image_validation, pdf_validation, data_required, phone_validation


class LoginForm(FlaskForm):
    _name = "Вход"
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

    def validate_password(self, password):
        user = User.query.filter_by(username=self.username.data).first()
        print(session.get("wrong_passwords"))
        if session.get("wrong_password_date") and (
                datetime.now() - datetime.fromisoformat(session["wrong_password_date"])).seconds < 5 * 60:
            raise ValidationError('Ошибка!')
        if not user or not user.check_password(self.password.data):
            if session.get("wrong_passwords") < 2:
                session["wrong_passwords"] += 1
            elif session["wrong_passwords"] >= 2 and not session.get("wrong_password_date"):
                session["wrong_password_date"] = datetime.now().isoformat()

            raise ValidationError('Неверное имя пользователя или пароль.')


class RegistrationForm(FlaskForm):
    _name = "Регистрация"
    username = StringField('Имя пользователя', validators=[DataRequired()])

    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повтор пароля', validators=[DataRequired()])
    # remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()

        if user:
            raise ValidationError('Это имя пользователя занято')
        elif username.data == app.config["DEFAULT_ADMIN_USERNAME"]:
            raise ValidationError('Это имя пользователя совпадает с базовым аккаунтом администратора!')

    def validate_password2(self, password):
        if password.data != self.password.data:
            raise ValidationError('Пароли не совпадают')


class CreateNewsForm(FlaskForm):
    _name = "Создать новость"
    title = StringField("Название поста:", validators=[DataRequired()])
    cover = FileField("Фотография:", validators=[DataRequired(), image_validation])
    body = CKEditorField("Текст поста:", validators=[DataRequired()])
    submit = SubmitField("Опубликовать")


class EditNewsForm(FlaskForm):
    _name = "Изменить новость"
    title = StringField("Название поста:", validators=[DataRequired()])
    cover = FileField("Фотография:", validators=[image_validation])
    body = CKEditorField("Текст поста:", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class CreateAchievementsForm(FlaskForm):
    _name = "Создать достижения"
    title = StringField("Название кск:", validators=[DataRequired()])
    body = CKEditorField("Текст:", validators=[DataRequired()])
    submit = SubmitField("Опубликовать")


class EditAchievementsForm(FlaskForm):
    _name = "Изменить достижения"
    title = StringField("Название кск:")
    body = CKEditorField("Текст:")
    submit = SubmitField("Сохранить")


class AddAnimalForm(FlaskForm):
    _name = "Добавить животное"
    name = StringField("Кличка нового животного:", validators=[DataRequired()])
    cover = FileField("Фотография:", validators=[DataRequired(), image_validation])
    for_sale = BooleanField("Продажная")
    body = CKEditorField("Информация о животном:", validators=[DataRequired()])
    submit = SubmitField("Добавить")


class EditAnimalForm(FlaskForm):
    _name = "Изменить животное"
    name = StringField("Кличка нового животного:", validators=[DataRequired()])
    cover = FileField("Фотография:", validators=[image_validation])
    for_sale = BooleanField("Продажная")
    body = CKEditorField("Информация о животном:", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class AddManureForm(FlaskForm):
    _name = "Добавить тип навоза"
    manure_type = StringField("Тип навоза", validators=[DataRequired()])
    cover = FileField("Фотография:", validators=[DataRequired(), image_validation])
    in_stock = BooleanField("В наличии")
    body = CKEditorField("Информация:", validators=[DataRequired()])
    submit = SubmitField("Добавить")


class EditManureForm(FlaskForm):
    _name = "Изменить тип навоза"
    manure_type = StringField("Тип навоза")
    cover = FileField("Фотография:", validators=[image_validation])
    in_stock = BooleanField("В наличии")
    body = CKEditorField("Информация:")
    submit = SubmitField("Сохранить")


class AddPartnerForm(FlaskForm):
    _name = "Добавить партнера"
    name = StringField("Имя партнёра:", validators=[DataRequired()])
    logo = FileField("Логотип партнёра:", validators=[DataRequired(), image_validation])
    link = URLField("Ссылка на партнёра")
    submit = SubmitField("Добавить")


class EditPartnerForm(FlaskForm):
    _name = "Изменить партнера"
    name = StringField("Имя партнёра:", validators=[DataRequired()])
    logo = FileField("Логотип партнёра:", validators=[image_validation])
    link = URLField("Ссылка на партнёра")
    submit = SubmitField("Сохранить")


class AddImageForm(FlaskForm):
    _name = "Добавить изображение"
    title = StringField("Название изображения", validators=[DataRequired()])

    image = FileField("Изображение", validators=[DataRequired(), image_validation])
    submit = SubmitField("Добавить")

    def validate_title(self, title):
        if Gallery.query.filter_by(title=title.data).all():
            raise ValidationError("Изображение с таким названием уже существует!")


class ConfigForm(FlaskForm):
    _name = "Настройки сайта"
    site_logo = FileField("Логотип сайта", validators=[image_validation])
    background_image = FileField("Фоновое изображение главной страницы", validators=[image_validation])
    allow_background_image = BooleanField("Отображать фоновое изображение")
    site_name = StringField("Название сайта")
    save = SubmitField("Сохранить")


class PageDataForm(FlaskForm):
    _name = "Изменить страницу"
    title = StringField("Заглавие страницы", validators=[DataRequired()])
    description = CKEditorField("Описание страницы", validators=[DataRequired()])
    save = SubmitField("Сохранить")


class EditContacts(FlaskForm):
    _name = "Редактировать контакты"
    phone_1 = StringField("Телефон №1", validators=[DataRequired(), phone_validation])
    phone_2 = StringField("Телефон №2", validators=[DataRequired(), phone_validation])
    email = EmailField("Электронная почта", validators=[DataRequired()])
    vk = URLField("Вк", validators=[DataRequired()])
    # ok = URLField("Одноклассники", validators=[DataRequired()])
    # dzen = URLField("Дзен", validators=[DataRequired()])
    save = SubmitField("Сохранить")

    def validate_vk_qr(self, field):
        if not Config.query.get("vk_group_qr"):
            raise ValidationError("This field is require.")


class AddPersonForm(FlaskForm):
    _name = "Добавить участника"
    name = StringField("Имя и фамилия:", validators=[DataRequired()])
    avatar = FileField("Фотография:", validators=[DataRequired(), image_validation])
    person_type = SelectField("Тип", choices=[("student", "Участник"), ("teacher", "Тренер")],
                              validators=[DataRequired()])
    submit = SubmitField("Добавить")


class EditPersonForm(FlaskForm):
    _name = "Изменить участника"
    name = StringField("Имя и фамилия:")
    avatar = FileField("Фотография:", validators=[image_validation])
    person_type = SelectField("Тип", choices=[("student", "Участник"), ("teacher", "Тренер")])
    submit = SubmitField("Сохранить")
