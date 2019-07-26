import os
from PIL import Image
import secrets
from flask import current_app
from datetime import datetime
from threading import Thread
from . import db
from .models import Moment, User
import json

# type与root path对应的字典，方便今后维护
root_path = {
    'user_profile_pic': 'static/profile_pic',
    'group_background': 'static/group_background_pic',
    'group_logo': 'static/group_logo',
    'post_cover_pic': 'static/post_cover_pic',
    'moment': 'static/moments'
}

# thread creator
def thr_saver(type, form_picture, user_id, **kwargs):
    print("first user = ", user_id)
    app = current_app._get_current_object()
    if type == 'moment':
        thr = Thread(target=moment_saver, args=[app, form_picture, user_id, kwargs['m_body'], kwargs['m_group'], kwargs['m_post']])
    thr.start()
    return thr

def moment_saver(app, form_pictures, user_id, body, group, post):
    print("user in moment_saver = ", user_id)
    with app.app_context():
        print("\nin app_context\n")
        print("user in moment_saver = ", user_id)
        print("body = ", body)
        pic_names = {}
        pic_index = 0
        for picture in form_pictures:
            pic_index += 1
            pic_names[str(pic_index)] = saver('moment', picture, user_id)
            picture.close()
        pic_names_str = json.dumps(pic_names)
        moment = Moment(body=body,
                        pictures=pic_names_str,
                        from_group=group,
                        from_post=post)
        db.session.add(moment)
        db.session.commit()

def saver(type, form_picture, user=None):

    print("\n in saver \n")
    print("User in saver = ", user)

    if type == 'user_profile_pic' and user is not None:
        random_hex = user.user_hex
    else:
        random_hex = secrets.token_hex(8)

    _, file_extension = os.path.splitext(form_picture.filename)
    picture_file_name = random_hex + file_extension

    _path = os.path.join(current_app.root_path, "static", picture_file_name)
    print("\n before save \n")
    form_picture.save(_path)
    form_picture.close()
    print("\n before open \n")
    i = Image.open(_path)
    print("\n after open \n")

    #form_picture.close()
    #i = Image.open(form_picture)
    #form_picture.close()

    if type == 'moment': # moments 需要存两份图片，一个缩略图，一个大图

        user_id = user
        group = User.query.get(user_id).my_group
        moment_dir = os.path.join(current_app.root_path, root_path[type], str(group.id))

        if not os.path.exists(moment_dir):
            os.mkdir(moment_dir)

        width, height = i.size

        # save picture of full size
        if width > 2000 or height > 2000:
            i.thumbnail([2000, 2000])
        full_picture_path = os.path.join(current_app.root_path, moment_dir, picture_file_name)
        i.save(full_picture_path)

        # save a thumbnail
        new_size = min(width, height)
        left = (width - new_size)/2
        top = (height - new_size)/2
        right = (width + new_size)/2
        bottom = (height + new_size)/2
        i = i.crop((left, top, right, bottom)) # crop to square
        i.thumbnail([250, 250]) # resize, no return
        thumbnail_file_name = "thumbnail_" + picture_file_name
        thumbnail_path = os.path.join(current_app.root_path, moment_dir, thumbnail_file_name)
        i.save(thumbnail_path)

    if type == 'user_profile_pic' or type == 'group_logo':

        width, height = i.size
        new_size = min(width, height)

        left = (width - new_size)/2
        top = (height - new_size)/2
        right = (width + new_size)/2
        bottom = (height + new_size)/2

        i = i.crop((left, top, right, bottom))
        i.thumbnail([250, 250])

        # save it to static folder
        picture_path = os.path.join(current_app.root_path, root_path[type], picture_file_name)
        i.save(picture_path)

    if type == 'group_background':
        width, height = i.size
        if width / height < 2.4: # if the image is too 'tall'
            new_height = int(width / 2.4)
            crop_len = (height - new_height) / 2

            left = 0
            right = width
            top = crop_len
            bottom = height - crop_len

            i = i.crop([left, top, right, bottom])

        if width > 2000: # if the image has too many pixels
            i.thumbnail([2000, 2000])

        picture_path = os.path.join(current_app.root_path, root_path[type], picture_file_name)
        i.save(picture_path)

    if type == 'post_cover_pic':
        width, height = i.size

        if height > (9/16) * width:
            new_height = int( (9/16) * width)
            crop_len = (height - new_height) / 2
            left = 0
            right = width
            top = crop_len
            bottom = height - crop_len
            i = i.crop([left, top, right, bottom])

        if width >= (16/9) * height:
            new_width = int( (16/9) * height)
            crop_len = (width - new_width) / 2
            left = crop_len
            right = width - crop_len
            top = 0
            bottom = height
            i = i.crop([left, top, right, bottom])
            width = new_width

        if width > 500:
            i.thumbnail([500, 500])

        picture_path = os.path.join(current_app.root_path, root_path[type], picture_file_name)
        i.save(picture_path)

    i.close()
    #os.remove(_path)

    return picture_file_name

def deleter(type, old_file_name, moment_dir=None): # moment_dir is the id of the group to which the moment belongs.
    if moment_dir:
        full_pic_path = os.path.join(current_app.root_path, root_path[type], str(moment_dir), old_file_name)
        thumbnail_path = os.path.join(current_app.root_path, root_path[type], str(moment_dir), 'thumbnail_%s' % old_file_name)
        os.remove(full_pic_path)
        os.remove(thumbnail_path)
    else:
        old_file_path = os.path.join(current_app.root_path, root_path[type], old_file_name)
        os.remove(old_file_path)
