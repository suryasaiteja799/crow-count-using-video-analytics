from models import db

def migrate():
    db.engine.execute('''
    ALTER TABLE video_record 
    ADD COLUMN zones TEXT,
    ADD COLUMN grid_size TEXT;
    ''')
    print("Added zones and grid_size columns to video_record table")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate()