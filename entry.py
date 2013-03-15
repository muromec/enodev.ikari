from ikari.main import app
from ikari.root import setup_root
from consoleargs import command

@command(positional='action')
def main(action='run'):
    app.config['DEBUG'] = True

    if action == 'run':
        app.run()
    elif action == 'root':
        with app.app_context():
            setup_root()

if __name__ == '__main__':
    main()    
