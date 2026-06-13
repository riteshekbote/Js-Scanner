import configparser
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

class ConfigManager:
    _config = None

    @classmethod
    def _clean_value(cls, value):
        """Strip inline comments (# onwards) and surrounding whitespace"""
        if not isinstance(value, str):
            return value
        sharp_pos = value.find('#')
        if sharp_pos != -1:
            value = value[:sharp_pos]
        return value.strip()

    @classmethod
    def load_config(cls):
        if cls._config is None:
            config = configparser.ConfigParser()
            if os.path.exists(CONFIG_FILE):
                config.read(CONFIG_FILE, encoding='utf-8')
            else:
                raise FileNotFoundError(f"Config file {CONFIG_FILE} not found, please create config.ini")
            cls._config = config
        return cls._config

    @classmethod
    def get_ai_config(cls):
        config = cls.load_config()
        # Get raw values and strip comments
        api_base_raw = config.get('AI', 'api_base', fallback='https://api.deepseek.com')
        api_key_raw = config.get('AI', 'api_key', fallback='')
        model_raw = config.get('AI', 'model', fallback='deepseek-chat')
        temperature_raw = config.get('AI', 'temperature', fallback='0.1')
        max_tokens_raw = config.get('AI', 'max_tokens', fallback='8192')
        min_conf_raw = config.get('AI', 'min_confidence', fallback='0.0')

        api_base = cls._clean_value(api_base_raw)
        api_key = cls._clean_value(api_key_raw)
        model = cls._clean_value(model_raw)
        temperature_str = cls._clean_value(temperature_raw)
        max_tokens_str = cls._clean_value(max_tokens_raw)
        min_conf_str = cls._clean_value(min_conf_raw)

        # Safe conversion
        try:
            temperature = float(temperature_str) if temperature_str else 0.1
        except ValueError:
            temperature = 0.1
        try:
            max_tokens = int(max_tokens_str) if max_tokens_str else 8192
        except ValueError:
            max_tokens = 8192
        try:
            min_confidence = float(min_conf_str) if min_conf_str else 0.0
        except ValueError:
            min_confidence = 0.0

        return {
            'api_base': api_base,
            'api_key': api_key,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'min_confidence': min_confidence
        }

    @classmethod
    def get_app_config(cls):
        config = cls.load_config()
        report_dir_raw = config.get('App', 'report_dir', fallback='reports')
        cache_dir_raw = config.get('App', 'cache_dir', fallback='js_cache')
        auto_open_raw = config.get('App', 'auto_open_report', fallback='false')

        report_dir = cls._clean_value(report_dir_raw)
        cache_dir = cls._clean_value(cache_dir_raw)
        auto_open_str = cls._clean_value(auto_open_raw)
        auto_open_report = auto_open_str.lower() in ('true', '1', 'yes')

        return {
            'report_dir': report_dir,
            'cache_dir': cache_dir,
            'auto_open_report': auto_open_report
        }
