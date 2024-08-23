from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from house.settings import EMAIL_HOST_USER, BASE_DIR
import os
import pickle
import random


@shared_task
def send_email(userEmail):
    code = random.randint(100000, 999999, )
    cache.set(userEmail, str(code), 60 * 10)
    send_mail(
        subject='房源管家:黄小耶',
        message='注册验证码为：{0}，10分钟内有效，请勿泄露和转发。如非本人操作，请忽略此信息。'.format(code),
        from_email=EMAIL_HOST_USER,
        recipient_list=[userEmail]
    )
    return '发送邮件成功：{0}'.format(userEmail)


def data_encode(input_data):
    input_list = []
    for key, value in input_data.items():
        if key == 'house_size':
            input_list.append(value)
        else:
            path = os.path.join(BASE_DIR, 'models\{0}.pkl'.format(key))
            with open(path, 'rb') as f:
                label = pickle.load(f)
                encode_data = label.transform([value])
                encode_data = int(encode_data[0])
                input_list.append(encode_data)
    return input_list


@shared_task
def predict_model(input_data):
    data = {}
    input_list = data_encode(input_data)
    path = os.path.join(BASE_DIR, 'models\house.pkl')
    with open(path, 'rb') as f:
        model = pickle.load(f)
        pred_y = model.predict([input_list])
        data['single_price'] = int(pred_y[0][0])
        data['total_price'] = int(pred_y[0][1])
        return data

