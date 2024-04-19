def write_user_to_env(id):
    with open('.env', mode='r') as file:
        text = file.readlines()
        text[-1] = text[-1].strip() + f',{str(id)}'
    with open('.env', mode='w') as file:
        file.writelines(text)
