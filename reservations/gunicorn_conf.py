from multiprocessing import cpu_count

# Socket Path
bind = 'unix:/home/ubuntu/VoiceAssistant-Backend/reservations/gunicorn.sock'

# Worker Options
workers =  1
# workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/home/ubuntu/VoiceAssistant-Backend/reservations/access_log'
errorlog =  '/home/ubuntu/VoiceAssistant-Backend/reservations/error_log'