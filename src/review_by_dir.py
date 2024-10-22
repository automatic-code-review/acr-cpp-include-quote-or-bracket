import review
import argparse
import json
import os

if __name__ == '__main__':
    with open('../config.json', 'r') as data:
        config = json.load(data)

    path_source = config['path_source']

    changes = []

    for root, dirs, files in os.walk(path_source):
        for file in files:
            if not file.endswith(('.cpp', '.h')):
                continue

            path = os.path.join(root, file)
            changes.append({
                "new_path": path.replace(path_source, "")[1:]
            })

    config['merge']['changes'] = changes

    comments = review.review(config)
    print(json.dumps(comments))
