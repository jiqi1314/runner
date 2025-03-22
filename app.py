from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 數據文件路徑
TODOS_FILE = 'todos.json'

# 加載待辦事項
def load_todos():
    try:
        if os.path.exists(TODOS_FILE):
            with open(TODOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f'Error loading todos: {e}')
    return []

# 保存待辦事項
def save_todos(todos):
    try:
        with open(TODOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(todos, f, ensure_ascii=False)
    except Exception as e:
        print(f'Error saving todos: {e}')

shared_todos = load_todos()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('init-todos', shared_todos)

@socketio.on('add-todo')
def handle_add_todo(todo):
    global shared_todos
    print('Received new todo:', todo)
    
    # 保存現有待辦事項狀態
    todo_states = [{
        'text': t['text'],
        'completed': t['completed'],
        'completedAt': t['completedAt'],
        'remark': t['remark']
    } for t in shared_todos]
    
    # 添加新待辦事項
    shared_todos.insert(0, todo)
    
    # 恢復原有待辦事項狀態
    for i in range(1, len(shared_todos)):
        shared_todos[i]['completed'] = todo_states[i-1]['completed']
        shared_todos[i]['completedAt'] = todo_states[i-1]['completedAt']
        shared_todos[i]['remark'] = todo_states[i-1]['remark']
    
    save_todos(shared_todos)
    emit('todos-updated', shared_todos, broadcast=True)

@socketio.on('toggle-todo')
def handle_toggle_todo(data):
    global shared_todos
    index = data['index']
    shared_todos[index]['completed'] = data['completed']
    shared_todos[index]['completedAt'] = data['completedAt']
    save_todos(shared_todos)
    emit('todos-updated', shared_todos, broadcast=True)

@socketio.on('update-remark')
def handle_update_remark(data):
    global shared_todos
    shared_todos[data['index']]['remark'] = data['remark']
    save_todos(shared_todos)
    emit('todos-updated', shared_todos, broadcast=True)

@socketio.on('reset-todos')
def handle_reset():
    global shared_todos
    shared_todos = []
    save_todos(shared_todos)
    emit('todos-updated', shared_todos, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)