from testapp import socketio,app

if __name__ == '__main__':
    # app.run(debug=True)
    # socketio.run(app, debug=True)
    socketio.run(app, host='192.168.2.36', debug=True)