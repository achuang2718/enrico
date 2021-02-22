:again
:: A hacky way of doing a while True loop in Windows batch language
ECHO updating time now, %date% %time%
START w32tm /resync
TIMEOUT /t 14400 /nobreak
GOTO again