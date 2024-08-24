from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QMouseEvent, QFont, QIcon
import sys

win_size = 250

'''
event planner:
    food:
        don't get hungry while sleeping
        every 20 min is hungry and in 1h it dies
    sleep:
        every 2h must have 15 minute sleep
        when tired it don't do tasks
    dead:
        dead for 15 minutes "waiting for resurection"
    tasks:
        fav:
            opens favourite soft
        reminder:
            reminds user of task to do in specified time
'''

def darken_pixmap(pixmap, darkening_factor=0.5):
    darkening_factor = max(0, min(1, darkening_factor))
    darkened_pixmap = QPixmap(pixmap.size())
    darkened_pixmap.fill(Qt.transparent)
    painter = QPainter(darkened_pixmap)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
    black_color = QColor(0, 0, 0, int(255 * darkening_factor))
    painter.fillRect(darkened_pixmap.rect(), black_color)
    painter.end()
    return darkened_pixmap

def get_screen_height():
    screen_geometry = QDesktopWidget().screenGeometry()
    screen_height = screen_geometry.height()
    return screen_height

class CMainWindow(QFrame):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle('Fun Bun')

        screen_height = get_screen_height()

        self.setFixedHeight(win_size)
        self.setFixedWidth(int(win_size + win_size//1.8))
        self.move(QPoint(0, screen_height - win_size))

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignLeft)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.avatar_display = QLabel()
        self.avatar_display.setFixedWidth(win_size)
        self.avatar_display.setFixedHeight(win_size)
        self.main_layout.addWidget(self.avatar_display)

        self.side_panel = QLabel()
        self.side_panel.setContentsMargins(0, 0, 0, 0)
        self.side_panel.setStyleSheet('''
                                      background: rgba(0,0,0,100);
                                      border-radius: 30px;
                                      ''')
        self.side_panel.setFixedWidth(int(win_size//1.8))
        self.side_panel.setFixedHeight(win_size)
        self.side_panel.hide()
        self.main_layout.addWidget(self.side_panel)
        
        self.food_btn = QPushButton()
        self.light_btn = QPushButton()
        self.light_on = True
        self.fav_btn = QPushButton()
        self.reminder_btn = QPushButton()

        for button, button_fun, icon in zip([self.food_btn, self.light_btn, self.fav_btn, self.reminder_btn],
                                            [self.food_fun, self.light_fun, self.fav_fun, self.reminder_fun],
                                            ['assets/images/icons/fish.png',
                                             'assets/images/icons/light/on.png',
                                             'assets/images/icons/hearth.png',
                                             'assets/images/icons/bell.png']):
            button.setFixedWidth(int(win_size//1.8))
            button.setFixedHeight(win_size//4)
            button.setIconSize(self.light_btn.size())
            button.clicked.connect(button_fun)
            if icon != None:
                button.setIcon(QIcon(icon))
            else:
                pass
            button.setStyleSheet('''QPushButton{
                                 border-radius: 30px;
                                 }
                                 QPushButton:hover{
                                 background: rgba(0, 0, 0, 35);
                                 }''')

        self.side_panel_layout = QVBoxLayout()
        self.side_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.side_panel_layout.setAlignment(Qt.AlignTop)
        self.side_panel.setLayout(self.side_panel_layout)
        self.c_set_side_pannel()

        self.animation_path = None
        self.animation_frames = None
        self.animation_intervals = None
        
        self.frame_index = 0
        self.animation_tick = QTimer(self)
        self.animation_tick.timeout.connect(self.animation_update)

        self.c_set_animation('idle')
        self.animation_tick.start()

        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.sleep_timer_timeout)
        self.setup_sleep_timer()

        self.fatigue_timer = QTimer(self)
        self.fatigue_timer.timeout.connect(self.fatigue_timeout)
        self.setup_fatigue_timer()

        self.hunger_timer = QTimer(self)
        self.setup_hunger_timer()

# ----------------------------------------------- sleepy time event  - in progress

    def setup_fatigue_timer(self):
        self.tired = False
        self.fatigue_timer.setInterval(1000 * 60 * 60 * 2)#                                 time
        self.fatigue_timer.start()

    def fatigue_timeout(self):
        self.fatigue_timer.stop()
        self.tired = True
        if self.animation_name == 'idle':
            self.c_set_animation('tired')

    def setup_sleep_timer(self):
        self.sleep_timer.setInterval(1000 * 60 * 15)#                                   time

    def sleep_timer_timeout(self):
        self.sleep_timer.stop()
        self.tired = False
        self.resume_hunger_timer()
        self.setup_sleep_timer()
        self.setup_fatigue_timer()

    def pause_sleep(self):
        remaining_time = self.sleep_timer.remainingTime()
        self.sleep_timer.stop()
        self.sleep_timer.setInterval(remaining_time)

    def start_sleep(self):
        self.c_set_animation('sleep')
        self.sleep_timer.start()

# -----------------------------------------------------------------

# ----------------------------------------------- hunger time event

    def setup_hunger_timer(self):
        self.hungry = False
        self.hunger_timer.stop()
        if self.tired:
            self.c_set_animation('tired')
        else:
            self.c_set_animation('idle')
        self.hunger_timer.setInterval(1000 * 60 * 20)#                                  time
        try:
            self.hunger_timer.timeout.disconnect()
        except:
            pass
        self.hunger_timer.timeout.connect(self.hunger_timeout)
        self.hunger_timer.start()

    def hunger_timeout(self):
        self.hungry = True
        self.hunger_timer.stop()
        self.c_set_animation('sad')
        self.hunger_timer.setInterval(1000 * 60 * 60)#                                   time
        self.hunger_timer.timeout.disconnect()
        self.hunger_timer.timeout.connect(self.die_fun)
        self.hunger_timer.start()
    
    def die_fun(self):
        self.hunger_timer.stop()
        self.c_set_animation('dead')
        self.hunger_timer.setInterval(1000 * 60 * 15)#                                   time
        self.hunger_timer.timeout.disconnect()
        self.hunger_timer.timeout.connect(self.cat_resurection)
        self.hunger_timer.start()
        
    def cat_resurection(self):
        self.setup_sleep_timer()
        self.setup_fatigue_timer()
        self.setup_hunger_timer()

    def pause_hunger_timer(self):
        remaining_time = self.hunger_timer.remainingTime()
        remaining_time += 1000 * 2#                                                time
        self.hunger_timer.stop()
        self.hunger_timer.setInterval(remaining_time)

    def resume_hunger_timer(self):
        if self.hungry:
            self.c_set_animation('sad')
        elif self.tired:
            self.c_set_animation('tired')
        else:
            self.c_set_animation('idle')
        self.hunger_timer.start()

# ---------------------------------------------------------------



# ----------------------------------------------------- buttons functions

    def fun_check(self, fun):
        if self.animation_name == 'dead':
            self.c_set_side_pannel('message', 'dead')
            return False
        if fun == 'light':
            return True
        if self.light_on:
            if fun == 'food' or self.animation_name != 'sad':
                if self.animation_name != 'tired':
                    return True
                else:
                    self.c_set_side_pannel('message', 'tired')
                    return False
            else:
                self.c_set_side_pannel('message', 'hungry')
                return False
        else:
            self.c_set_side_pannel('message', 'too dark')
            return False

    def food_fun(self):
        if self.fun_check('food'):
            if self.animation_name == 'sad':
                self.setup_hunger_timer()

    def light_fun(self):
        if self.fun_check('light'):
            if self.light_on:
                self.light_on = False
                self.light_btn.setIcon(QIcon('assets/images/icons/light/off.png'))
                if self.animation_name == 'tired':
                    self.pause_hunger_timer()
                    self.start_sleep()
            else:
                self.light_on = True
                self.light_btn.setIcon(QIcon('assets/images/icons/light/on.png'))
                if self.animation_name == 'sleep':
                    self.pause_sleep()
                    self.resume_hunger_timer()
            
            self.animation_tick.stop()
            if self.frame_index == 0:
                self.frame_index = len(self.animation_frames)-1
            else:
                self.frame_index -= 1
            self.animation_update(update_time = False)
            self.animation_tick.start()
    
    def fav_fun(self):
        if self.fun_check('fav'):
            self.c_set_side_pannel('fav_panel')
    
    def reminder_fun(self):
        if self.fun_check('reminder'):
            print('reminder')

# ---------------------------------------------------------------------


    def c_set_side_pannel(self, type = 'normal', message = ''):
        def remove_widgets_from_pannel(pannel):
            pannel.setAlignment(Qt.AlignTop)
            while pannel.count():
                item = pannel.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    pannel.removeWidget(widget)
                    widget.setParent(None)

        if type == 'normal':
            self.side_panel.setStyleSheet('''
                                      background: rgba(0,0,0,100);
                                      border-radius: 30px;
                                      ''')
            remove_widgets_from_pannel(self.side_panel_layout)
            self.side_panel_layout.addWidget(self.food_btn)
            self.side_panel_layout.addWidget(self.fav_btn)
            self.side_panel_layout.addWidget(self.light_btn)
            self.side_panel_layout.addWidget(self.reminder_btn)

        elif type == 'message':
            self.side_panel.setStyleSheet('''
                                      background: black;
                                      border-radius: 30px;
                                      ''')
            remove_widgets_from_pannel(self.side_panel_layout)
            message_label = QLabel()
            message_label.setStyleSheet('background: rgba(0, 0, 0, 0)')
            message_label.setFixedWidth(138)
            message_label.setFixedHeight(185)
            message_label.setPixmap(QPixmap('assets/images/messages/' + message + '.png'))

            message_ok_btn = QPushButton('ok')
            message_ok_btn.setFixedWidth(int(win_size//1.8))
            message_ok_btn.setFixedHeight(60)
            message_ok_btn.setStyleSheet('''QPushButton{
                                         background: white;
                                         }
                                         QPushButton:hover{
                                         background: rgba(255, 255, 255, 120)
                                         }
                                         ''')
            message_ok_btn.clicked.connect(lambda _:self.c_set_side_pannel())

            self.side_panel_layout.addWidget(message_label)
            self.side_panel_layout.addWidget(message_ok_btn)
        
        elif type == 'fav_panel':
            self.side_panel.setStyleSheet('''
                                      background: rgba(0,0,0,100);
                                      border-radius: 30px;
                                      ''')
            remove_widgets_from_pannel(self.side_panel_layout)
            self.side_panel_layout.setAlignment(Qt.AlignBottom)

            open_fav_btn = QPushButton('no fav selected')
            open_fav_btn.setFixedHeight(90)
            open_fav_btn.setFixedWidth(138)

            change_fav_btn = QPushButton('change fav')
            change_fav_btn.setFixedHeight(60)
            change_fav_btn.setFixedWidth(138)

            back_btn = QPushButton('back')
            back_btn.setFixedWidth(138)
            back_btn.setFixedHeight(60)
            
            btn_list = [open_fav_btn, change_fav_btn]
            for button in btn_list:
                button.setStyleSheet('''QPushButton{
                                     background: rgba(255, 255, 255, 130);
                                     color: black;
                                     }
                                     QPushButton:hover{
                                     background: white;
                                     }''')
                
            back_btn.setStyleSheet('''QPushButton{
                                   background: white;
                                   color: black;
                                   }
                                   QPushButton:hover{
                                   background: rgba(255, 255, 255, 120)
                                   }
                                   ''')
            
            self.side_panel_layout.addWidget(open_fav_btn)
            self.side_panel_layout.addWidget(change_fav_btn)
            self.side_panel_layout.addSpacerItem(QSpacerItem(1, 28))
            self.side_panel_layout.addWidget(back_btn)
            back_btn.clicked.connect(lambda _:self.c_set_side_pannel())

    def c_set_animation(self, animation_name):

        animation_list = ['idle', 'tired', 'sleep', 'sad', 'dead']
        if animation_name not in animation_list:
            raise Exception(f'No animation called {animation_name}')
        
        self.frame_index = 0
        self.animation_name = animation_name

        if animation_name == 'idle':
            self.animation_path = 'assets/images/idle/'
            self.animation_frames = ['open', 'left', 'open', 'right', 'open',
                                    'half closed', 'closed', 'half closed', 'open',
                                    'half closed', 'closed', 'half closed', 'open',
                                    'half closed', 'closed', 'half closed', 'open']
            self.animation_intervals = [2000, 1000, 50, 800, 5000,
                                        50, 50, 70, 7000,
                                        50, 50, 70, 7000,
                                        50, 50, 70, 7000]
        
        elif animation_name == 'sad':
            self.animation_path = 'assets/images/sad/'
            self.animation_frames = ['open', 'left', 'open', 'right', 'open',
                                    'half closed', 'closed', 'half closed', 'open',
                                    'half closed', 'closed', 'half closed', 'open',
                                    'half closed', 'closed', 'half closed', 'open']
            self.animation_intervals = [2000, 1000, 50, 800, 5000,
                                        50, 50, 70, 7000,
                                        50, 50, 70, 7000,
                                        50, 50, 70, 7000]
            
        elif animation_name == 'tired':
            self.animation_path = 'assets/images/tired/'
            self.animation_frames = ['open', 'closed']
            self.animation_intervals = [6000, 300]

        elif animation_name == 'sleep':
            self.animation_path = 'assets/images/asleep/'
            self.animation_frames = ['closed']
            self.animation_intervals = [10000]

        elif animation_name == 'dead':
            self.animation_path = 'assets/images/dead/'
            self.animation_frames = ['dead']
            self.animation_intervals = [10000]

        image = self.animation_path
        image += self.animation_frames[0] + '.png'
        self.avatar_display.setPixmap(QPixmap(image))

        self.animation_tick.setInterval(0)
        
    def animation_update(self, update_time = True):

        id = self.frame_index
        if update_time:
            self.animation_tick.setInterval(self.animation_intervals[id])
        image = self.animation_path
        image += self.animation_frames[id] + '.png'
        image = QPixmap(image)
        if not self.light_on:
            image = darken_pixmap(image)
        self.avatar_display.setPixmap(image)
        self.frame_index += 1
        if self.frame_index == len(self.animation_frames):
            self.frame_index = 0

    def mouseDoubleClickEvent(self, event):
        if self.side_panel.isVisible():
            self.side_panel.hide()
        else:
            self.side_panel.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.winPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.side_panel.isVisible() == False:
                delta = QPoint(event.globalPos() - self.winPos)
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.winPos = event.globalPos()
            else:
                pass

AppHandler = QApplication(sys.argv)

App = CMainWindow()
App.show()
sys.exit(AppHandler.exec_())