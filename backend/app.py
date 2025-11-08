"""
Flask 백엔드 서버 메인 애플리케이션
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from dotenv import load_dotenv
from api.events import events_bp
from api.alerts import alerts_bp

# 환경변수 로드
load_dotenv()

# Flask 앱 생성
app = Flask(__name__)

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    # 로그 파일 경로
    log_file = os.path.join(os.path.dirname(__file__), 'server.log')

    # 로그 포맷
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 파일 핸들러 (5MB, 백업 3개)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Flask 로거 설정
    app.logger.setLevel(logging.INFO)

    return logging.getLogger('app')


# 로거 초기화
logger = setup_logging()

# Blueprint 등록
app.register_blueprint(events_bp)
app.register_blueprint(alerts_bp)


# 루트 엔드포인트 (헬스체크)
@app.route('/', methods=['GET'])
def health_check():
    """헬스체크 API"""
    return jsonify({
        'status': 'healthy',
        'service': 'Error Notification System',
        'version': '1.0.0'
    }), 200


# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# 서버 실행
if __name__ == '__main__':
    # 환경변수에서 포트 가져오기
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info("=" * 80)
    logger.info("🚀 Error Notification System 백엔드 서버 시작")
    logger.info(f"   포트: {port}")
    logger.info(f"   디버그 모드: {debug}")
    logger.info("=" * 80)

    # Flask 서버 실행
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
