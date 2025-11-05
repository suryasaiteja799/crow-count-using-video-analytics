import os
from datetime import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, VideoRecord, LoginHistory, create_app_db, hash_password

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crow_counter.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)

    # ensure upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize DB (create tables and default admin) immediately
    create_app_db(app)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember') == 'on'
            # simple validation
            if not email or not password:
                flash('Please provide email and password', 'warning')
                # record failed attempt
                try:
                    lh = LoginHistory(email=email or '', success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                    db.session.add(lh)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return render_template('login.html')
            user = User.query.filter_by(email=email.strip().lower()).first()
            if user:
                if not user.is_active:
                    flash('Account blocked. Contact an administrator.', 'danger')
                    try:
                        lh = LoginHistory(email=user.email, success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                        db.session.add(lh)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    return render_template('login.html')
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                # record success
                try:
                    lh = LoginHistory(user_id=user.id, email=user.email, success=True, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                    db.session.add(lh)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            # invalid credentials
            try:
                lh = LoginHistory(email=email or '', success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                db.session.add(lh)
                db.session.commit()
            except Exception:
                db.session.rollback()
            flash('Invalid email or password', 'danger')
        return render_template('login.html')

    @app.route('/admin-login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            if not email or not password:
                flash('Please provide email and password', 'warning')
                try:
                    lh = LoginHistory(email=email or '', success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                    db.session.add(lh)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return render_template('admin_login.html')

            email_norm = email.strip().lower()
            user = User.query.filter_by(email=email_norm).first()

            if user and not user.is_active:
                flash('Account blocked. Contact an administrator.', 'danger')
                try:
                    lh = LoginHistory(email=user.email, success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                    db.session.add(lh)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return render_template('admin_login.html')

            # If user exists, check password hash and admin flags
            if user and (user.is_admin or user.is_super_admin) and check_password_hash(user.password_hash, password):
                login_user(user)
                try:
                    lh = LoginHistory(user_id=user.id, email=user.email, success=True, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                    db.session.add(lh)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                flash('Admin logged in successfully', 'success')
                # redirect super-admins to their dashboard
                if user.is_super_admin:
                    return redirect(url_for('super_admin_dashboard'))
                return redirect(url_for('admin'))

            # If user does not exist but matches our known default credentials, create them (hashed)
            DEFAULTS = [
                {'email': 'suryasaiteja799@gmail.com', 'password': 'surya@799', 'is_super': True, 'is_admin': True},
                {'email': '23kq1a6350@pace.ac.in', 'password': 'Teja@6350', 'is_super': False, 'is_admin': True},
            ]
            for d in DEFAULTS:
                if email_norm == d['email'] and password == d['password']:
                    # create user
                    new_user = User(name='Super Admin' if d['is_super'] else 'Admin', email=d['email'], password_hash=generate_password_hash(d['password']), is_admin=d['is_admin'], is_super_admin=d['is_super'])
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
                    try:
                        lh = LoginHistory(user_id=new_user.id, email=new_user.email, success=True, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                        db.session.add(lh)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    flash('Admin logged in successfully', 'success')
                    if new_user.is_super_admin:
                        return redirect(url_for('super_admin_dashboard'))
                    return redirect(url_for('admin'))

            # failed
            flash('Invalid admin credentials', 'danger')
            try:
                lh = LoginHistory(email=email or '', success=False, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                db.session.add(lh)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return render_template('admin_login.html')

    @app.route('/super-admin/toggle-block/<int:user_id>', methods=['POST'])
    @login_required
    def super_admin_toggle_block(user_id):
        # Only super admins may block/unblock accounts
        if not current_user.is_super_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'warning')
            return redirect(url_for('super_admin_dashboard'))
        # Prevent blocking other super admins or yourself
        if user.is_super_admin:
            flash('Cannot block another super admin', 'warning')
            return redirect(url_for('super_admin_dashboard'))
        if user.id == current_user.id:
            flash('You cannot block your own account', 'warning')
            return redirect(url_for('super_admin_dashboard'))

        user.is_active = not user.is_active
        try:
            db.session.commit()
            flash('User {} successfully.'.format('unblocked' if user.is_active else 'blocked'), 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update user: ' + str(e), 'danger')
        return redirect(url_for('super_admin_dashboard'))

    @app.route('/super-admin')
    @login_required
    def super_admin_dashboard():
        if not current_user.is_super_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        users = User.query.all()
        videos = VideoRecord.query.all()
        login_history = LoginHistory.query.order_by(LoginHistory.created_at.desc()).all()
        return render_template('super_admin.html', 
                             users=users, 
                             videos=videos, 
                             login_history=login_history)

    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin and not current_user.is_super_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        users = User.query.filter(User.is_super_admin.is_(False)).all()
        videos = VideoRecord.query.all()
        return render_template('admin.html', users=users, videos=videos)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            # validation
            if not name or not email or not password:
                flash('All fields are required', 'warning')
                return render_template('register.html')
            if len(password) < 6:
                flash('Password must be at least 6 characters', 'warning')
                return render_template('register.html')
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'warning')
                return render_template('register.html')

            user = User(name=name, email=email, password_hash=hash_password(password), is_admin=False)
            try:
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash('Failed to register user: ' + str(e), 'danger')
                return render_template('register.html')
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        records = VideoRecord.query.filter_by(user_id=current_user.id).order_by(VideoRecord.created_at.desc()).all()
        return render_template('dashboard.html', records=records)

    @app.route('/upload', methods=['POST'])
    @login_required
    def upload():
        if 'video' not in request.files:
            flash('No video uploaded', 'warning')
            return redirect(url_for('dashboard'))
        file = request.files['video']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Invalid file', 'warning')
            return redirect(url_for('dashboard'))
        filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_" + file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        # create DB record as pending
        rec = VideoRecord(user_id=current_user.id, filename=filename, status='pending')
        db.session.add(rec)
        db.session.commit()

        # try to enqueue Celery task if available
        try:
            from tasks import process_video_task
            process_video_task.apply_async(args=(rec.id, path))
            flash('Uploaded successfully. Processing queued.', 'info')
        except Exception:
            # fallback to inline processing
            try:
                from video_process import process_video
                total_count = process_video(path)
                rec.total_count = total_count
                rec.status = 'completed'
                rec.processed_at = datetime.utcnow()
                db.session.commit()
                flash(f'Uploaded and processed inline. Estimated count: {total_count}', 'success')
            except Exception as e:
                rec.status = 'failed'
                rec.error_message = str(e)
                db.session.commit()
                flash('Processing failed: ' + str(e), 'danger')

        return redirect(url_for('dashboard'))

    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/video/<int:video_id>/preview')
    @login_required
    def video_preview(video_id):
        video = VideoRecord.query.get_or_404(video_id)
        # Check if user has permission to view this video
        if video.user_id != current_user.id and not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard'))
        return render_template('video_preview.html', video=video)

    @app.route('/api/zones', methods=['POST'])
    @login_required
    def save_zones():
        try:
            data = request.get_json()
            video_id = data.get('videoId')
            zones = data.get('zones')
            grid_size = data.get('gridSize')

            video = VideoRecord.query.get_or_404(video_id)
            if video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'})

            # Save zones and grid data to the video record
            video.zones = json.dumps(zones)
            video.grid_size = json.dumps(grid_size)
            db.session.commit()

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/analyze/<int:video_id>', methods=['POST'])
    @login_required
    def analyze_video(video_id):
        try:
            video = VideoRecord.query.get_or_404(video_id)
            if video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'})
            # Get the saved zones and grid size
            zones = json.loads(video.zones) if video.zones else []
            grid_size = json.loads(video.grid_size) if video.grid_size else {'x': 4, 'y': 3}

            # optional mode parameter: 'motion' (default) or 'yolo'
            mode = None
            if request.is_json:
                mode = (request.get_json() or {}).get('mode')
            if not mode:
                mode = request.args.get('mode') or 'motion'

            # Build absolute path to video file
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'Video file not found on disk'})

            # Lazy import analyzer to avoid import errors if opencv missing earlier
            try:
                from analyzer import analyze_video_file, analyze_video_with_yolo
            except Exception as e:
                return jsonify({'success': False, 'error': f'Analyzer import failed: {e}'})

            # Run analysis (may take time)
            try:
                if mode == 'yolo':
                    results = analyze_video_with_yolo(video_path, zones=zones, grid_size=grid_size, max_frames=800, sample_rate=3)
                else:
                    results = analyze_video_file(video_path, zones=zones, grid_size=grid_size, max_frames=800, sample_rate=3)
            except Exception as e:
                # Update video status to error
                video.status = 'error'
                video.error_message = str(e)
                db.session.commit()
                return jsonify({'success': False, 'error': f'Analysis failed: {e}'})

            # Update the video record with the total count
            video.total_count = results.get('total_count', 0)
            video.processed_at = datetime.now()
            video.status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'results': results
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    # --- Background job support for async analysis ---
    import threading
    import uuid

    # Simple in-memory job store: {job_id: {status, progress, result, error}}
    jobs = {}

    def _run_analysis_job(job_id, video_id, video_path, zones, grid_size):
        # determine mode (default motion)
        mode = jobs.get(job_id, {}).get('mode', 'motion')
        jobs[job_id]['status'] = 'running'
        try:
            from analyzer import analyze_video_file, analyze_video_with_yolo
            # update progress marker
            jobs[job_id]['progress'] = 0
            # Run the analysis (synchronous call) — analyzer returns results dict
            if mode == 'yolo':
                results = analyze_video_with_yolo(video_path, zones=zones, grid_size=grid_size)
            else:
                results = analyze_video_file(video_path, zones=zones, grid_size=grid_size)
            jobs[job_id]['result'] = results
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 100

            # store summary into DB
            try:
                video = VideoRecord.query.get(video_id)
                if video:
                    video.total_count = results.get('total_count', 0)
                    video.processed_at = datetime.now()
                    video.status = 'completed'
                    db.session.commit()
                    # also save results.json to uploads/detections/<video_id>/result.json for dashboard
                    try:
                        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'detections', str(video_id))
                        os.makedirs(save_dir, exist_ok=True)
                        import json as _json
                        with open(os.path.join(save_dir, 'result.json'), 'w', encoding='utf-8') as _f:
                            _json.dump(results, _f)
                        # move any images returned into this folder as well (if analyzer saved elsewhere)
                        if isinstance(results.get('images'), list):
                            for p in results.get('images'):
                                try:
                                    if os.path.exists(p):
                                        basename = os.path.basename(p)
                                        dst = os.path.join(save_dir, basename)
                                        if not os.path.exists(dst):
                                            import shutil
                                            shutil.copy2(p, dst)
                                except Exception:
                                    pass
                    except Exception:
                        pass
            except Exception:
                # don't crash job if DB write fails
                pass

        except Exception as e:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['progress'] = 0
            # mark DB record as error
            try:
                video = VideoRecord.query.get(video_id)
                if video:
                    video.status = 'error'
                    video.error_message = str(e)
                    db.session.commit()
            except Exception:
                pass

    @app.route('/api/analyze/start', methods=['POST'])
    @login_required
    def start_analysis():
        try:
            data = request.get_json() or {}
            video_id = data.get('videoId') or request.form.get('videoId')
            mode = data.get('mode') or request.form.get('mode') or 'motion'
            if not video_id:
                return jsonify({'success': False, 'error': 'videoId required'}), 400

            video = VideoRecord.query.get_or_404(int(video_id))
            if video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'}), 403

            zones = json.loads(video.zones) if video.zones else []
            grid_size = json.loads(video.grid_size) if video.grid_size else {'x': 4, 'y': 3}

            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'Video file not found on disk'}), 404

            job_id = str(uuid.uuid4())
            jobs[job_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None, 'video_id': video.id, 'mode': mode}
            thread = threading.Thread(target=_run_analysis_job, args=(job_id, video.id, video_path, zones, grid_size), daemon=True)
            thread.start()

            return jsonify({'success': True, 'job_id': job_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/analyze/status/<job_id>', methods=['GET'])
    @login_required
    def analysis_status(job_id):
        job = jobs.get(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        # Only allow owner or admin to query
        try:
            vid = job.get('video_id')
            video = VideoRecord.query.get(vid) if vid else None
            if video and video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        except Exception:
            pass

        return jsonify({'success': True, 'job': {'status': job['status'], 'progress': job.get('progress', 0), 'result': job.get('result'), 'error': job.get('error')}})

    @app.route('/api/video/<int:video_id>/info', methods=['GET'])
    @login_required
    def video_info(video_id):
        video = VideoRecord.query.get_or_404(video_id)
        if video.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        return jsonify({'success': True, 'video': {
            'id': video.id,
            'filename': video.filename,
            'status': video.status,
            'total_count': video.total_count,
            'zones': json.loads(video.zones) if video.zones else [],
            'grid_size': json.loads(video.grid_size) if video.grid_size else None
        }})

    @app.route('/api/detect_preview/<int:video_id>', methods=['POST'])
    @login_required
    def detect_preview(video_id):
        """Run a short YOLO detection preview on the video (synchronous).

        JSON body (optional): { sample_rate: int, max_frames: int, classes: [names], save_frames: bool }
        Returns JSON with results and images (if saved).
        """
        try:
            video = VideoRecord.query.get_or_404(video_id)
            if video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'}), 403

            params = request.get_json() or {}
            sample_rate = int(params.get('sample_rate', 5))
            max_frames = int(params.get('max_frames', 20))
            classes = params.get('classes')
            save_frames = bool(params.get('save_frames', True))

            zones = json.loads(video.zones) if video.zones else []
            grid_size = json.loads(video.grid_size) if video.grid_size else {'x': 4, 'y': 3}
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'Video file not found on disk'}), 404

            try:
                from analyzer import analyze_video_with_yolo
            except Exception as e:
                return jsonify({'success': False, 'error': f'Analyzer import failed: {e}'}), 500

            # output dir for saved images
            out_dir = None
            if save_frames:
                out_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'detections_preview')
                os.makedirs(out_dir, exist_ok=True)

            results = analyze_video_with_yolo(video_path, zones=zones, grid_size=grid_size, max_frames=max_frames, sample_rate=sample_rate, classes=classes, save_frames=save_frames, out_dir=out_dir)

            # If images are returned as absolute paths under uploads, convert to URLs
            images = []
            for p in results.get('images', []):
                # if path is under UPLOAD_FOLDER, make relative
                try:
                    rel = os.path.relpath(p, app.config['UPLOAD_FOLDER'])
                    images.append(url_for('uploaded_file', filename=rel))
                except Exception:
                    images.append(p)
            # Save results JSON into out_dir for dashboard consumption
            try:
                if save_frames and out_dir:
                    import json as _json
                    with open(os.path.join(out_dir, 'result.json'), 'w', encoding='utf-8') as f:
                        _json.dump(results, f)
            except Exception:
                pass

            return jsonify({'success': True, 'results': results, 'images': images})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/detect_regions/<int:video_id>', methods=['POST'])
    @login_required
    def detect_regions(video_id):
        """Run detection for specified rectangular regions on an image/video preview.

        Expects JSON: { rects: [ {x,y,w,h}, ... ], classes: [...], save: bool }
        """
        try:
            video = VideoRecord.query.get_or_404(video_id)
            if video.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'}), 403

            data = request.get_json() or {}
            rects = data.get('rects') or []
            classes = data.get('classes')
            save = bool(data.get('save', True))

            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'File not found'}), 404

            try:
                from analyzer import detect_image, point_in_poly
            except Exception as e:
                return jsonify({'success': False, 'error': f'Analyzer import failed: {e}'}), 500

            # run detection on image (we assume image input for region detection)
            out_dir = None
            if save:
                out_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'detections', str(video_id))
                os.makedirs(out_dir, exist_ok=True)
                out_img = os.path.join(out_dir, 'regions_annotated.jpg')
            else:
                out_img = None

            det_res = detect_image(video_path, classes=classes, out_path=out_img)
            dets = det_res.get('detections', [])

            # Filter detections to rects
            def in_any_rect(cx, cy, rects_list):
                for r in rects_list:
                    x = r.get('x'); y = r.get('y'); w = r.get('w'); h = r.get('h')
                    if cx >= x and cx <= x + w and cy >= y and cy <= y + h:
                        return True
                return False

            width = None
            # get image size
            try:
                import cv2 as _cv
                img = _cv.imread(video_path)
                width = img.shape[1]
                height = img.shape[0]
            except Exception:
                width = None

            # compute counts
            zone_list = json.loads(video.zones) if video.zones else []
            zone_counts = {i: 0 for i in range(len(zone_list))}
            grid = json.loads(video.grid_size) if video.grid_size else {'x':4,'y':3}
            grid_counts = {}
            for gy in range(grid['y']):
                for gx in range(grid['x']):
                    grid_counts[f"{chr(65+gy)}{gx+1}"] = 0

            matched = []
            for d in dets:
                cx = int((d['x1'] + d['x2']) / 2)
                cy = int((d['y1'] + d['y2']) / 2)
                if rects and not in_any_rect(cx, cy, rects):
                    continue
                matched.append(d)
                # zone counts
                for zi, zone in enumerate(zone_list):
                    if point_in_poly(cx, cy, zone.get('points', zone)):
                        zone_counts[zi] += 1
                # grid cell
                if width:
                    gx = min(grid['x'] - 1, int(cx / (width / grid['x'])))
                    gy = min(grid['y'] - 1, int(cy / (height / grid['y'])))
                    cell_id = f"{chr(65+gy)}{gx+1}"
                    grid_counts[cell_id] = grid_counts.get(cell_id, 0) + 1

            resp = {
                'matched_count': len(matched),
                'matched': matched,
                'zone_counts': zone_counts,
                'grid_counts': grid_counts,
                'annotated_image': url_for('uploaded_file', filename=os.path.relpath(out_img, app.config['UPLOAD_FOLDER'])) if out_img else None
            }

            # save result.json
            try:
                if out_dir:
                    import json as _json
                    with open(os.path.join(out_dir, 'result.json'), 'w', encoding='utf-8') as f:
                        _json.dump({'total_count': resp['matched_count'], 'grid_counts': grid_counts, 'zone_counts': zone_counts}, f)
            except Exception:
                pass

            return jsonify({'success': True, 'result': resp})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out', 'info')
        return redirect(url_for('login'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
