from flask import Flask, jsonify
from tasks import parse_website_task

app = Flask(__name__)

@app.route('/')
def home():
    return "<h3>Docker Scraper Project is Running!</h3>"

@app.route('/test-task')
def trigger_task():
    task = parse_website_task.delay("http://google.com")
    return jsonify({"message": "Task started", "task_id": task.id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
