import os
from PIL import Image
import secrets
from flask import current_app

# type与root path对应的字典，方便今后维护
root_path = {
    'user_profile_pic': 'static/profile_pic',
    'group_background': 'static/group_background_pic',
    'group_logo': 'static/group_logo',
    'event_cover_pic': 'static/event_cover_pic'
}

def saver(type, form_picture, user=None):

    if type == 'user_profile_pic' and user is not None:
        random_hex = user.user_hex
    else:
        random_hex = secrets.token_hex(8)

    _, file_extension = os.path.splitext(form_picture.filename)
    picture_file_name = random_hex + file_extension

    i = Image.open(form_picture)

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
            height = new_height

        if width > 2000: # if the image has too many pixels
            i.thumbnail([2000, 2000])

        picture_path = os.path.join(current_app.root_path, root_path[type], picture_file_name)
        i.save(picture_path)

    if type == 'event_cover_pic':
        pass

    return picture_file_name

def deleter(type, old_file_name):
    old_file_path = os.path.join(current_app.root_path, root_path[type], old_file_name)
    os.remove(old_file_path)
