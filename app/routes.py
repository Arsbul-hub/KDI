import os
import random
import string
from urllib.parse import urlsplit

from flask import render_template, send_from_directory, url_for, flash, redirect, request
from flask_ckeditor import upload_fail, upload_success
from app import app, morph
from PIL import Image
from flask_login import current_user, login_user, logout_user, login_required
from app.models import *
from app.forms import *
from werkzeug.urls import url_parse
from app import login
from flask import session

from bs4 import BeautifulSoup


def load_file(name):
    try:
        return Image.open("app/" + name)

    except FileNotFoundError:
        return None


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/files/<path:filename>')
def uploaded_files(filename):
    return send_from_directory("static/loaded_media", filename)


@app.route('/reload_auth')
def reload_auth_system():
    messages = ["Конфигурационный файл аутентификации пользователей был перезагружен!"]
    admin = User.query.filter_by(username="Admin").first()
    if admin:
        admin.username = app.config["DEFAULT_ADMIN_USERNAME"]
        admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])

    else:
        admin = User()
        admin.username = app.config["DEFAULT_ADMIN_USERNAME"]
        admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
        db.session.add(admin)

    db.session.commit()
    logout_user()

    return render_template("service/Уведомление.html", title="Внимание", messages=messages)


@app.route('/upload', methods=['POST', "GET"])
def upload():
    f = request.files.get('upload')
    # Add more validations here
    save_file(f)

    url = url_for('uploaded_files', filename=f.filename)

    return upload_success(url, filename=f.filename)


def namegen(size=6):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))


def save_file(file, path="", name=None, service_path=""):
    full_path = "static/loaded_media"
    extension = file.filename.split('.')[-1].lower()
    file.filename = namegen(8).replace(" ", "") + "." + extension
    if service_path:
        full_path = f"static/{service_path}"

    if name:
        file.filename = name.replace(' ', '')
    if path and not os.path.exists(f"app/static/loaded_media/{path}"):
        os.makedirs(f"app/static/loaded_media/{path}")

    if "image" in file.content_type and "svg+xml" not in file.content_type:
        image = Image.open(file)
        if image.width > 2000:
            require_width = 2000  # Уменьшенный размер (ширина)
            new_size = require_width, int((float(image.size[1]) * float((require_width / float(image.size[0])))))
            image = image.resize(new_size, Image.LANCZOS)

        elif image.height > 1300:
            require_height = 1300  # Уменьшенный размер (высота)
            new_size = int((float(image.size[0]) * float((require_height / float(image.size[1]))))), require_height
            image = image.resize(new_size, Image.LANCZOS)
        image.save(f"app/{full_path}/{path}/{file.filename}")
    else:
        file.save(f"app/{full_path}/{path}/{file.filename}")
    return f"static/loaded_media/{path}/{file.filename}"


def remove_file(path):
    if os.path.exists("app/" + path):
        os.remove("app/" + path)


@app.route('/')
@app.route("/index")
def index():
    print(request.args.get("is_xhr"))
    data = PagesData.query.get("index")
    allow_background_image = False
    site_name = ""
    if Config.query.filter_by(category="config").all():
        allow_background_image = Config.query.get("allow_background_image").value
        site_name = Config.query.get("site_name").value
    return render_template("index.html", user=current_user, site_data=data, site_name=site_name,
                           allow_background_image=allow_background_image)


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@login_required
@app.route("/delete_user")
def delete_user():
    user = User.query.get(request.args.get("id"))
    if user and user.username != app.config["DEFAULT_ADMIN_USERNAME"]:
        logout_user()
        db.session.delete(user)
        db.session.commit()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if session.get("wrong_password_date") and (
            datetime.now() - datetime.fromisoformat(session["wrong_password_date"])).seconds >= 5 * 60:
        session.pop("wrong_password_date")
        session.pop("wrong_passwords")
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    else:
        session["wrong_passwords"] = 0
    return render_template('forms/login.html', user=current_user, title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # login_user(user, remember=form.remember_me.data)
        flash('Congratulations, you are now a registered admin!')
        return redirect(url_for('index'))
    return render_template('forms/register.html', user=current_user, title='Register', form=form)


@app.route("/Панель управления")
@login_required
def admin_panel():
    return render_template("admin_panel.html", user=current_user, admin_username=app.config["DEFAULT_ADMIN_USERNAME"])


@app.route("/Настройки сайта", methods=["GET", "POST"])
@login_required
def site_settings():
    form = ConfigForm()

    if form.validate_on_submit():

        save_file(file=form.site_logo.data, service_path="images", name="logo.png")
        save_file(file=form.background_image.data, service_path="images", name="background_image.png")

        Config.query.get("allow_background_image").value = form.allow_background_image.data
        Config.query.get("site_name").value = form.site_name.data
        db.session.commit()
        return redirect(url_for("admin_panel"))
    else:
        if Config.query.filter_by(category="config").all():
            form.allow_background_image.data = int(Config.query.get("allow_background_image").value)
            form.site_name.data = Config.query.get("site_name").value
        else:
            db.session.add(Config(key="allow_background_image", value=False, category="config"))
            db.session.add(Config(key="site_name", value="", category="config"))
            db.session.commit()
    return render_template("forms/site_settings.html", user=current_user, config=Config, form=form)


# @login_required
# @app.route("/Файловый менеджер")
# def file_manager():
#     filemanager_link = url_for('flaskfilemanager.index')
#     print(filemanager_link)
#     return redirect(filemanager_link)


@login_required
@app.route("/Изменить страницу", methods=["GET", "POST"])
def edit_page_description():
    form = PageDataForm()
    page = request.args.get("page")
    page_name = request.args.get("page_name")
    if form.validate_on_submit():
        if PagesData.query.get(page):
            data = PagesData.query.get(page)
            data.description = form.description.data
            data.title = form.title.data
        else:
            data = PagesData()
            data.page = page
            data.description = form.description.data
            data.title = form.title.data
            db.session.add(data)
        db.session.commit()
        return redirect(url_for(page))
    elif PagesData.query.get(page):
        form.description.data = PagesData.query.get(page).description

        form.title.data = PagesData.query.get(page).title
    return render_template("forms/edit_page_description.html", user=current_user, form=form, page_name=page_name)


@app.route("/Добавить новость", methods=['GET', 'POST'])
@login_required
def add_news():
    action = request.args.get("action")

    form = CreateNewsForm()
    if action == "edit":
        form = EditNewsForm()
        news_post = News.query.get(request.args.get("id"))
        if news_post:
            if form.validate_on_submit():
                news_post.title = form.title.data
                news_post.body = form.body.data
                if form.cover.data:
                    news_post.cover = save_file(form.cover.data)
                db.session.commit()
                return redirect(url_for("news"))
            else:
                form.title.data = news_post.title
                form.body.data = news_post.body
        else:
            return redirect(url_for("news"))
    elif form.validate_on_submit():
        saved_cover = save_file(file=form.cover.data)
        news_post = News(title=form.title.data, body=form.body.data, cover=saved_cover)
        db.session.add(news_post)
        db.session.commit()
        flash('Вы опубликовали новый пост!')
        return redirect(url_for("news"))
    return render_template("forms/add_news.html", user=current_user, form=form)


@app.route("/Новости")
def news():
    action = request.args.get('action')

    print(action)
    if action == "show":
        news_list = News.query.get(request.args.get('id'))
        return render_template("show_news.html", user=current_user, news=news_list)
    elif current_user.is_authenticated and action == "remove":
        news = News.query.get(request.args.get('id'))
        remove_file(news.cover)
        db.session.delete(news)

        db.session.commit()
        return redirect(url_for("news"))

    news = News.query.all()

    news_list = list(filter(lambda n: (datetime.today() - n.timestamp).total_seconds() < 3600 * 24 * 10, news))
    old_news_list = list(filter(lambda n: (datetime.today() - n.timestamp).total_seconds() > 3600 * 24 * 10, news))

    return render_template("news.html", user=current_user, BeautifulSoup=BeautifulSoup, news=news_list,
                           old_news=old_news_list,
                           morph=morph, today=datetime.today(),
                           case={"gent"})


@app.route("/Добавить животное", methods=['GET', 'POST'])
@login_required
def add_animal():
    action = request.args.get("action")

    form = AddAnimalForm()
    if action == "edit":
        form = EditAnimalForm()
        animal = Animals.query.get(request.args.get("id"))
        if animal:
            if form.validate_on_submit():
                animal.name = form.name.data
                animal.body = form.body.data
                animal.for_sale = form.for_sale.data
                if form.cover.data:
                    animal.cover = save_file(form.cover.data)
                db.session.commit()
                return redirect(request.args.get("previous"))
            else:
                form.name.data = animal.name
                form.body.data = animal.body
                form.for_sale.data = animal.for_sale
        else:
            return redirect(request.args.get("previous"))
    elif form.validate_on_submit():
        out_path = save_file(file=form.cover.data)

        new_animal = Animals(name=form.name.data, body=form.body.data, for_sale=form.for_sale.data, cover=out_path)
        db.session.add(new_animal)
        db.session.commit()
        flash('Вы добавили новое животное!')
        return redirect(request.args.get("previous"))
    return render_template("forms/add_animal.html", user=current_user, form=form)


@app.route('/Наши животные')
def our_animals():
    action = request.args.get('action')
    if current_user.is_authenticated and action:
        if action == "remove":
            db.session.delete(Animals.query.get(request.args.get('id')))

            db.session.commit()

        return redirect(request.args.get("previous"))

    animals = Animals.query.all()

    return render_template("our_animals.html", BeautifulSoup=BeautifulSoup, animals=animals,
                           user=current_user)


@app.route('/Лошади на продаже')
def for_sale_animals():
    action = request.args.get('action')
    if current_user.is_authenticated and action:
        if action == "remove":
            db.session.delete(Animals.query.get(request.args.get('id')))

            db.session.commit()

        return redirect(request.args.get("previous"))

    animals = Animals.query.filter_by(for_sale=True).all()

    return render_template("for_sale_animals.html", BeautifulSoup=BeautifulSoup, animals=animals,
                           user=current_user)


@app.route("/Добавить изображение", methods=['GET', 'POST'])
@login_required
def add_image_to_gallery():
    action = request.args.get("action")
    form = AddImageForm()

    if form.validate_on_submit():
        out_path = save_file(file=form.image.data)
        image = Gallery(title=form.title.data, file=out_path)
        db.session.add(image)
        db.session.commit()
        return redirect(url_for("gallery"))
    return render_template("forms/add_image.html", user=current_user, form=form)


@app.route("/Галерея")
def gallery():
    action = request.args.get('action')
    if current_user.is_authenticated and action:
        if action == "remove":
            image = Gallery.query.get(request.args.get('id'))
            db.session.delete(image)
            remove_file(image.file)
            db.session.commit()

        return redirect(url_for("gallery"))

    return render_template("gallery.html", user=current_user, gallery_list=Gallery.query.all())


@login_required
@app.route("/Редактировать контакты", methods=["GET", "POST"])
def edit_contacts():
    form = EditContacts()
    if form.validate_on_submit():
        if Config.query.filter_by(category="contacts").all():
            Config.query.get("email").value = form.email.data
            Config.query.get("phone_1").value = form.phone_1.data
            Config.query.get("phone_2").value = form.phone_1.data
            Config.query.get("vk_url").value = form.vk.data
            # Config.query.get("ok_url").value = form.ok.data
            # Config.query.get("dzen_url").value = form.dzen.data
        else:
            db.session.add(Config(key="email", value=form.email.data, category="contacts"))

            db.session.add(Config(key="phone_1", value=form.phone_1.data, category="contacts"))
            db.session.add(Config(key="phone_2", value=form.phone_1.data, category="contacts"))
            db.session.add(Config(key="vk_url", value=form.vk.data, category="contacts"))
            # db.session.add(Config(key="ok_url", value=form.ok.data, category="contacts"))
            # db.session.add(Config(key="dzen_url", value=form.dzen.data, category="contacts"))
        db.session.commit()
        return redirect(url_for("contacts"))
    else:

        if Config.query.filter_by(category="contacts").all():
            form.email.data = Config.query.get("email").value
            form.phone_1.data = Config.query.get("phone_number_1").value
            form.phone_2.data = Config.query.get("phone_number_2").value
            form.vk.data = Config.query.get("vk_url").value
            # form.ok.data = Config.query.get("ok_url").value
            # form.dzen.data = Config.query.get("dzen_url").value
    return render_template("forms/edit_contacts.html", user=current_user, form=form)


@app.route("/Контакты")
def contacts():
    email, phone_1, phone_2, vk = "", "", "", ""
    if Config.query.filter_by(category="contacts").all():
        email = Config.query.get("email").value
        phone_1 = Config.query.get("phone_1").value
        phone_2 = Config.query.get("phone_2").value
        vk = Config.query.get("vk_url").value
        # ok = Config.query.get("ok_url").value
        # dzen = Config.query.get("dzen_url").value
    return render_template("contacts.html", user=current_user, vk=vk, email=email, phone_1=phone_1, phone_2=phone_2)


@app.route("/Катание на лошадях")
def horse_riding():
    data = PagesData.query.get("horse_riding")

    return render_template("horse_riding.html", user=current_user, site_data=data)


@app.route("/Пргулки в экипаже")
def crew_riding():
    data = PagesData.query.get("crew_riding")

    return render_template("crew_riding.html", user=current_user, site_data=data)


@app.route("/Иппотерапия")
def hippotherapy():
    data = PagesData.query.get("hippotherapy")

    return render_template("hippotherapy.html", user=current_user, site_data=data)


@app.route("/Добавить тип навоза", methods=['GET', 'POST'])
@login_required
def add_manure_type():
    action = request.args.get("action")

    form = AddManureForm()
    if action == "edit":
        form = EditManureForm()
        animal = Manure.query.get(request.args.get("id"))
        if animal:
            if form.validate_on_submit():
                animal.name = form.manure_type.data
                animal.body = form.body.data
                animal.in_stock = form.in_stock.data
                if form.cover.data:
                    animal.cover = save_file(form.cover.data)
                db.session.commit()
                return redirect(request.args.get("previous"))
            else:
                form.manure_type.data = animal.name
                form.body.data = animal.body
                form.in_stock.data = animal.in_stock
        else:
            return redirect(request.args.get("previous"))
    elif form.validate_on_submit():
        out_path = save_file(file=form.cover.data)

        new_animal = Manure(name=form.manure_type.data, body=form.body.data, in_stock=form.in_stock.data,
                            cover=out_path)
        db.session.add(new_animal)
        db.session.commit()

        return redirect(request.args.get("previous"))
    return render_template("forms/add_manure.html", user=current_user, form=form)


@app.route('/Конский навоз')
def manure():
    action = request.args.get('action')
    if current_user.is_authenticated and action:
        if action == "remove":
            db.session.delete(Manure.query.get(request.args.get('id')))

            db.session.commit()

        return redirect(request.args.get("previous"))

    manure_types = Manure.query.all()

    return render_template("manure.html", BeautifulSoup=BeautifulSoup, manure_types=manure_types,
                           user=current_user)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html', user=current_user), 404

