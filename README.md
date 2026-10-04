# t8ot
A modern, lightweight framework for building modular Telegram bots with telebot.

```
t8ot/
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── examples/
│   ├── basic_bot.py
│   └── modular_bot/
│       ├── handlers/
│       │   ├── __init__.py
│       │   └── start.py
│       └── main.py
└── src/
    └── t8ot/
        ├── __init__.py
        ├── app.py
        ├── context.py 
        ├── router.py  
        ├── types/    
        │   ├── __init__.py
        │   └── keyboards.py
        ├── fsm/
        │   ├── __init__.py
        │   ├── states.py
        │   └── storage.py
        └── middlewares/
            ├── __init__.py
            └── base.py         
```