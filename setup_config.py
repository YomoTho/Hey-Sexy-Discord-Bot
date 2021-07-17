import json
import os

CONFIG_JSON_PATH='data/config.json'


if __name__ == '__main__':
    if not os.path.exists(CONFIG_JSON_PATH):
        with open(CONFIG_JSON_PATH, 'w+') as f:
            f.write(r"{}")

        config = dict()

        config['disable_channels'] = []
        config['stats'] = False
        config['prefix'] = '.'

        with open(CONFIG_JSON_PATH, 'w') as f:
            json.dump(config, f, indent=4)

        print('Done with config.json.')
    else:
        print(CONFIG_JSON_PATH, 'already exists.')
