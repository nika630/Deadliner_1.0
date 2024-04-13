# -*- coding: utf-8 -*-

# Deadliner 1.0
# Планировщик дел
# developed on PyQt5

import sys, res, res_log
import sqlite3

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QTreeWidgetItem, \
    QListWidgetItem, QInputDialog, QCalendarWidget, QMessageBox, QWidget, QGraphicsDropShadowEffect


class MyCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        QCalendarWidget.__init__(self, parent)
        self.dates = None

    def setDates(self, dates):
        self.dates = dates[:]
        self.updateCells()

    def paintCell(self, painter, rect, date):
        QCalendarWidget.paintCell(self, painter, rect, date)
        if date in self.dates:
            painter.setBrush(QtGui.QColor(185, 71, 216, 70))
            painter.setPen(QtGui.QColor(0, 0, 0, 0))
            painter.drawRect(rect)


class Deadliner(QMainWindow):  # главное окно
    def __init__(self, user):
        super(Deadliner, self).__init__()
        self.user = user[0][0]
        print('userid', self.user)
        self.sql = None
        self.db = None
        self.not_save_part_task = False
        self.del_pt_flag = False
        uic.loadUi('design/main_window.ui', self)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('icon/logo.png'))
        self.setWindowTitle('Deadliner 1.0')
        self.db = sqlite3.connect('deadliner.db')
        self.sql = self.db.cursor()

        self.user_name = self.sql.execute('''SELECT login FROM users WHERE rowid = ?''', (self.user,)).fetchall()
        self.hiWindow.setText(f' Привет, {self.user_name[0][0]}')
        self.hiWindow.setToolTip('Вы можете сменить пользователя \n'
                                 'вкладка "Управление"')
        self.helpButton.setToolTip('Помощь')
        self.change_user.setToolTip('Сменить пользователя')

        self.sql.execute("""CREATE TABLE IF NOT EXISTS Tasks(
            user_id INT,
            task_name TEXT,
            deadline TEXT,
            part_tasks INT,
            start_day TEXT
        )""")

        self.db.commit()

        self.calendarWidget = MyCalendar(self)
        self.calendarWidget.setGeometry(40, 200, 401, 320)
        self.start_date = self.calendarWidget.selectedDate()
        self.now_date = self.calendarWidget.selectedDate()
        self.dateEdit.setDate(self.start_date)
        self.calendarWidget.clicked.connect(self.on_clicked_calendar)
        self.dateEdit.dateChanged.connect(self.on_date_edit_change)
        self.progressBar.setProperty('value', 0)
        self.part_tasks = []

        self.rewrite_tree_widget()
        # КНОПКИ
        self.save.clicked.connect(self.save_changes)  # кнопка сохранения задачи
        self.newButton.clicked.connect(self.new)  # новая задача
        self.allButton.clicked.connect(self.rewrite_tree_widget)  # показать все задачи
        self.treeWidget.clicked.connect(self.read_task)  # просмотр сохраненных задач
        self.add_part_task.clicked.connect(self.part_task_maker)  # кнопка добавления подзадачи
        self.deleteButton.clicked.connect(self.delete_file)  # удаление задачи
        self.del_part_task.clicked.connect(self.delItem_listWidget)  # удаление подзадачи
        self.helpButton.clicked.connect(self.about_deadliner)  # помощь
        self.change_user.clicked.connect(self.reg)  # сменить пользователя

        # МЕНЮ
        self.user_change.triggered.connect(self.reg)
        self.actionNew.triggered.connect(self.new)
        self.actionDel.triggered.connect(self.delete_file)
        self.actionSave.triggered.connect(self.save_changes)
        self.actionExit.triggered.connect(self.close_deadliner)
        self.actionDelpretask.triggered.connect(self.delItem_listWidget)
        self.about.triggered.connect(self.about_deadliner)
        self.calendar.triggered.connect(self.about_calendar)
        self.creator.triggered.connect(self.about_creator)
        self.viewer.triggered.connect(self.about_viewer)

        self.generate()  # Генерируем список дат текущего месяца для подсветки
        self.listWidget.setWordWrap(True)

    def about_deadliner(self, event):
        msg_deadliner = QMessageBox(self)
        msg_deadliner.setWindowTitle('Hi, user!')
        msg_deadliner.setText(f'{self.user_name[0][0]},\n'
                              f'Добро пожаловать в Deadliner! \n'
                              f'Я помогу быстро справиться с задачами к поставленному сроку и ничего не забыть.')
        msg_deadliner.setInformativeText('Рассказать что я могу и как мною управлять?')
        msg_deadliner.setIconPixmap(QPixmap("icon/logo.png").scaled(400, 300, Qt.KeepAspectRatio))
        msg_deadliner.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_result = msg_deadliner.exec_()
        if msg_result == QMessageBox.Yes:
            msg_drive = QMessageBox(self)
            msg_drive.setWindowTitle('Управление!')
            msg_drive.setText('Dealiner состоит из 3х главных полей: \n'
                              '1. Поле календаря \n'
                              '2. Поле редактирования задач \n'
                              '3. Поле просмотра дедлайнов \n'
                              'О их возможностях вы можете узнать в разделе "Справка"')
            msg_drive.setInformativeText('Перейти в раздел "Поле календаря"?')
            msg_drive.setIconPixmap(QPixmap("icon/fields.png").scaled(400, 300, Qt.KeepAspectRatio))
            msg_drive.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_result = msg_drive.exec_()
            if msg_result == QMessageBox.Yes:
                self.about_calendar()
            else:
                msg_drive.close()

    def about_calendar(self):
        msg_calendar = QMessageBox(self)
        msg_calendar.setWindowTitle('Календарь')
        msg_calendar.setText('Если вы добавите задачу, то дата дедлайна будет отображаться в календаре цветом. \n'
                             'Если вы нажмёте на дату отмеченную цветом, '
                             'то вы сможете просмотреть задачи за текущее число \n'
                             'Чтобы вернуться к просмотру всех задач, нажмите кнопку "Все задачи"')
        msg_calendar.setInformativeText('Перейти в раздел "Редактирование задач"?')
        msg_calendar.setIconPixmap(QPixmap("icon/calendar.png").scaled(400, 300, Qt.KeepAspectRatio))
        msg_calendar.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_result = msg_calendar.exec_()
        if msg_result == QMessageBox.Yes:
            self.about_creator()
        else:
            msg_calendar.close()

    def about_creator(self):
        msg_creator = QMessageBox(self)
        msg_creator.setWindowTitle('Редактирование задач')
        msg_creator.setText('Вы можете разбить задачу на подзадачи,'
                            'выполнение которых можно отмечать галочкой. \n'
                            'Если все подзадачи выполнены, то задача считается выполненной '
                            'и меняет свой цвет на зеленый. \n'
                            'Подзадачи можно редактировать двойным щелчком мыши. \n'
                            'Шкала внизу отражает сколько дней осталось до дедлайна в процентном соотношении, '
                            'а в окне "Осталось дней" - количество дней до дедлайна')
        msg_creator.setInformativeText('Перейти в раздел "Просмотр дедлайнов"?')
        msg_creator.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_creator.setIconPixmap(QPixmap("icon/redactor.png").scaled(400, 300, Qt.KeepAspectRatio))
        msg_result = msg_creator.exec_()
        if msg_result == QMessageBox.Yes:
            self.about_viewer()
        else:
            msg_creator.close()

    def about_viewer(self):
        msg_viewer = QMessageBox(self)
        msg_viewer.setWindowTitle('Просмотр дедлайнов')
        msg_viewer.setText('Добавленные задачи могут иметь 4 цвета:  \n'
                           '- красный: дедлайн прошел и задача не выполнена  \n'
                           '- оранжевый: осталось меньше 2х дней до дедлайна  \n'
                           '- синий: задача на выполнении \n'
                           '- зелены: задача выполнена \n'
                           'Окна "Истёк срок" и "На выполнении" отражают информацию о всех задачах')
        msg_viewer.setStandardButtons(QMessageBox.Ok)
        msg_viewer.setIconPixmap(QPixmap("icon/viewer.png").scaled(400, 300, Qt.KeepAspectRatio))
        msg_viewer.exec_()

    def generate(self):
        result = self.sql.execute("""SELECT deadline FROM Tasks WHERE user_id=?""", (self.user,)).fetchall()
        dates = []
        for i, row in enumerate(result):
            date = QDate.fromString(result[i][0], "d-MM-yyyy")
            dates.append(date)
        self.calendarWidget.setDates(dates)  # Передаем даты в наш календарь

    def rewrite_tree_widget(self):
        self.treeWidget.clear()
        self.calendarWidget.setSelectedDate(self.now_date)
        self.result = self.sql.execute("""SELECT * FROM Tasks WHERE user_id=?""", (self.user,)).fetchall()
        self.tree_widget_display()

    def tree_widget_display(self):
        self.treeWidget.clear()
        self.miss_deadline = 0
        self.in_work = 0
        for i, row in enumerate(self.result):
            state = []
            self.taskList = QTreeWidgetItem(self.treeWidget, [row[2], row[1]])
            if row[3]:
                part_tasks = row[3].split(';')
                state = [int(ii.split('#')[1]) for ii in part_tasks]
            calc_date = QDate.fromString(row[2], "d-MM-yyyy")
            days_total = self.start_date.daysTo(calc_date)
            if state and all(state):  # задача выполнена
                self.taskList.setBackground(0, QtGui.QColor("#b5ff23"))
                self.taskList.setBackground(1, QtGui.QColor("#b5ff23"))
            elif 0 < days_total <= 2:  # два дня и меньше до дедлайна
                self.taskList.setBackground(0, QtGui.QColor("#ffb38f"))
                self.taskList.setBackground(1, QtGui.QColor("#ffb38f"))
                self.in_work += 1
            elif days_total <= 0:  # дедлайн пропущен
                self.taskList.setBackground(0, QtGui.QColor("#ff8181"))
                self.taskList.setBackground(1, QtGui.QColor("#ff8181"))
                self.miss_deadline += 1
            else:
                self.taskList.setBackground(0, QtGui.QColor("#90d6fe"))
                self.taskList.setBackground(1, QtGui.QColor("#90d6fe"))
                self.in_work += 1

        self.miss_deadline_LCD.display(self.miss_deadline)
        self.in_work_LCD.display(self.in_work)

        self.db.commit()

    def new(self):  # новая задача
        self.task_title.setText('')
        self.listWidget.clear()
        self.calendarWidget.showToday()
        self.dateEdit.setDate(self.start_date)
        self.generate()

    def prodress(self):
        delta_days_left = self.create_date.daysTo(self.now_date)
        self.total = self.create_date.daysTo(self.deadline)
        if self.total == 0:
            self.percent = 100
        else:
            self.percent = int(delta_days_left * 100 / self.total)
        self.progressBar.setProperty('value', self.percent)

    def save_task(self):  # сохранение заметки и отображение
        self.part_tasks = []  # сохранение подзадач
        item = self.listWidget.item
        for ii in range(self.listWidget.count()):
            data = item(ii).text() + '#' + str(item(ii).checkState())
            self.part_tasks.append(data)
        self.part_tasks = ';'.join(self.part_tasks)

        task_name = self.task_title.text()
        self.deadline = self.calendarWidget.selectedDate().toString('dd-MM-yyyy')
        self.create_date = self.start_date.toString('dd-MM-yyyy')
        self.not_save_part_task = False

        # Добавление задачи в БД
        self.db.commit()
        result = self.sql.execute("""SELECT task_name FROM Tasks WHERE user_id=?""", (self.user,)).fetchall()
        if all((task_name,) != i for i in result):
            self.sql.execute("""INSERT INTO Tasks VALUES(?, ?, ?, ?, ?)""",
                             (self.user, task_name, self.deadline, self.part_tasks, self.create_date))
        else:
            self.sql.execute("""UPDATE Tasks SET deadline = ?, part_tasks = ? WHERE task_name = ? and user_id=?""",
                             (self.deadline, self.part_tasks, task_name, self.user))

        self.db.commit()
        self.rewrite_tree_widget()
        self.deadline = QDate.fromString(self.deadline, "d-MM-yyyy")
        self.create_date = QDate.fromString(self.create_date, "d-MM-yyyy")
        self.prodress()
        self.generate()

    def read_task(self):
        task_name = self.task_title.text()
        result = self.sql.execute("""SELECT task_name FROM Tasks WHERE user_id=?""", (self.user,)).fetchall()
        if all((task_name,) != i for i in result) and task_name != '':
            msg = QMessageBox(self)
            msg.setWindowTitle('Сохранить')
            msg.setText(f'Задача "{task_name}" не сохранена')
            msg.setInformativeText('Сохранить задачу?')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_result = msg.exec_()
            if msg_result == QMessageBox.Yes:
                self.calendarWidget.setSelectedDate(self.dateEdit.date())
                self.save_task()
            elif msg_result == QMessageBox.No:
                print('No')
                self.not_save_part_task = False
                self.read_task()
        elif self.not_save_part_task:
            msg = QMessageBox(self)
            msg.setWindowTitle('Сохранить')
            msg.setText('Имеются несохраненные подзадачи')
            msg.setInformativeText(f'Сохранить текущие изменения задачи "{task_name}"?')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_result = msg.exec_()
            if msg_result == QMessageBox.Yes:
                self.calendarWidget.setSelectedDate(self.dateEdit.date())
                self.save_task()
            elif msg_result == QMessageBox.No:
                print('No')
                self.not_save_part_task = False
                self.read_task()
        elif self.del_pt_flag:
            msg = QMessageBox(self)
            msg.setWindowTitle('Сохранить')
            msg.setText('Имеются несохраненные изменения')
            msg.setInformativeText(f'Сохранить текущие изменения задачи "{task_name}"?')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_result = msg.exec_()
            if msg_result == QMessageBox.Yes:
                self.calendarWidget.setSelectedDate(self.dateEdit.date())
                self.save_task()
                self.del_pt_flag = False
            elif msg_result == QMessageBox.No:
                print('No')
                self.del_pt_flag = False
                self.read_task()
        else:
            file = self.treeWidget.selectedItems()[0].text(1)
            result = self.sql.execute("""SELECT * FROM Tasks WHERE task_name = ? and user_id = ?""",
                                      (file, self.user)).fetchall()
            try:
                self.create_date = QDate.fromString(result[0][4], "d-MM-yyyy")
                self.deadline = QDate.fromString(result[0][2], "d-MM-yyyy")
                self.calendarWidget.setSelectedDate(self.deadline)
                self.dateEdit.setDate(self.deadline)
                self.task_title.setText(result[0][1])
                self.days_total = self.start_date.daysTo(self.deadline)
                self.days.display(self.days_total)
                self.listWidget.clear()
                try:
                    self.prodress()
                except:
                    print('Ошибка отображения ProgressBar')
                if result[0][2]:
                    part_tasks = result[0][3].split(';')
                    for i in part_tasks:
                        ii = i.split('#')
                        item = QListWidgetItem()
                        if int(ii[1]):
                            item.setCheckState(2)
                        else:
                            item.setCheckState(0)
                        item.setText(ii[0])
                        item.setFlags(
                            Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
                        self.listWidget.addItem(item)
            except:
                print('Ошибка выбора задачи из TreeWidget')

    def delete_file(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Удалить')
        msg.setText('Удалить текущую задачу?')
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_result = msg.exec_()
        if msg_result == QMessageBox.Ok:
            file = self.treeWidget.selectedItems()[0].text(1)
            self.sql.execute("""DELETE FROM Tasks WHERE task_name = ? and user_id = ?""", (file, self.user))
            self.db.commit()
            self.rewrite_tree_widget()
            self.new()
            self.days.display(0)

    def delItem_listWidget(self):
        try:
            msg = QMessageBox(self)
            msg.setWindowTitle('Удаление')
            msg.setText(f'Удалить подзадачу {self.listWidget.selectedItems()[0].text()}?')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_result = msg.exec_()
            if msg_result == QMessageBox.Yes:
                self.listWidget.takeItem(self.listWidget.row(self.listWidget.selectedItems()[0]))
                self.del_pt_flag = True
        except:
            print('Ошибка удаления подзадачи')
            msg = QMessageBox(self)
            msg.setWindowTitle('Ошибка')
            msg.setText(f'Выберите подзадачу для удаления')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def changeItem_listWidget(self):
        part_task, ok_pressed = QInputDialog.getText(self, "Подзадача",
                                                     "Редактировать подзадачу")
        if ok_pressed and part_task:
            item = self.listWidget.selectedItems()
            print(item)
            # item.setCheckState(False)
            item.setText(part_task)
            self.listWidget.addItem(item)

    def on_clicked_calendar(self):  # клики по календарю calendarWidget
        self.dateEdit.setDate(self.calendarWidget.selectedDate())
        self.deadline = self.calendarWidget.selectedDate()
        delta_days = self.start_date.daysTo(self.deadline)
        print('дней до дэдлайна', delta_days)
        self.days.display(delta_days)

        # отображение задач только на выбранный в календаре день
        deadline = self.calendarWidget.selectedDate().toString('dd-MM-yyyy')
        self.result = self.sql.execute("""SELECT * FROM Tasks WHERE deadline = ? and user_id = ?""",
                                       (deadline, self.user)).fetchall()
        self.tree_widget_display()

    def on_date_edit_change(self):  # клики по dateEdit
        self.deadline = self.dateEdit.date()
        self.calendarWidget.setSelectedDate(self.dateEdit.date())
        delta_days = self.start_date.daysTo(self.deadline)
        self.days.display(delta_days)

    def part_task_maker(self):
        part_task, ok_pressed = QInputDialog.getText(self, "Подзадача",
                                                     "Введите подзадачу")
        if ok_pressed and part_task:
            item = QListWidgetItem()
            item.setCheckState(False)
            item.setText(part_task)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
            self.listWidget.addItem(item)
            self.not_save_part_task = True

    def add_item(self, text):
        item = QListWidgetItem(text)
        item.setCheckState(False)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        self.listWidget.addItem(item)

    def save_changes(self):
        if self.task_title.text() == '':
            error = QMessageBox(self)
            error.setWindowTitle('Ошибка')
            error.setText('Ошибка сохранения задачи')
            error.setInformativeText('Введите название задачи')
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.exec_()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle('Сохранить')
            msg.setText('Сохранить задачу?')
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            result = msg.exec_()
            if result == QMessageBox.Yes:
                self.calendarWidget.setSelectedDate(self.dateEdit.date())
                self.save_task()
            elif result == QMessageBox.No:
                print('No')
                self.read_task()

    def close_deadliner(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Выход')
        msg.setText('Вы действительно хотите завершить работу Deadliner?')
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_result = msg.exec_()
        if msg_result == QMessageBox.Yes:
            self.db.close()
            self.close()

    def reg(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Сменить пользователя')
        msg.setText('Выйти и сохранить?')
        user_name = self.sql.execute('''SELECT login FROM users WHERE rowid = ?''', (self.user,)).fetchall()[0][0]
        msg.setInformativeText(f'Иначе несохраненные изменения пользователя "{user_name}" будут утеряны')
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg_result = msg.exec_()
        if msg_result == QMessageBox.Yes:
            self.save_task()
            change = LogIN()
            change.show()
            self.db.close()
            self.hide()
        elif msg_result == QMessageBox.No:
            change = LogIN()
            change.show()
            self.db.close()
            self.hide()


class LogIN(QWidget):
    def __init__(self):
        super(LogIN, self).__init__()
        uic.loadUi('design/login.ui', self)

        self.checkBox.stateChanged.connect(self.remember)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.db = sqlite3.connect('deadliner.db')
        self.sql = self.db.cursor()

        self.sql.execute("""CREATE TABLE IF NOT EXISTS users(
                login TEXT,
                password TEXT,
                state INT
                )""")
        self.db.commit()

        resutl = self.sql.execute('''SELECT login, password FROM users WHERE state = 2''').fetchall()
        if resutl:
            if len(resutl) == 1:
                self.LoginEdit.setText(resutl[0][0])
                self.PasswordEdit.setText(resutl[0][1])
                self.checkBox.setCheckState(2)
            else:
                print('существует больше одного логина с функцией запомнить пароль')
        else:
            print('нет сохраненных логинов')

        self.loginBtn.clicked.connect(
            lambda: self.logInProcess(self.LoginEdit.text(), self.PasswordEdit.text()))

        self.close_btn.clicked.connect(self.exit_log)

        self.RegisterButton.clicked.connect(
            lambda: self.RegProcess(self.LoginEdit.text(), self.PasswordEdit.text()))
        self.label.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=0, color=QtGui.QColor(234, 221, 186, 100)))
        self.label_2.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=0, color=QtGui.QColor(234, 221, 186, 100)))
        self.label_3.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=0, color=QtGui.QColor(234, 221, 186, 100)))
        self.loginBtn.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=0, color=QtGui.QColor(234, 221, 186, 100)))

    def remember(self):
        if self.checkBox.checkState() == 0:
            self.sql.execute('''UPDATE users SET state = 0''')
            self.db.commit()

    def logInProcess(self, loginEdit, passwordEdit):
        user_login = loginEdit
        user_password = passwordEdit
        if not user_login or not user_password:
            msg = QMessageBox.information(
                self,
                'Ошибка',
                'Введите логин и пароль'
            )
            return

        self.sql.execute(
            "SELECT login, password FROM users WHERE login=?",
            (user_login,))
        count = self.sql.fetchone()
        self.db.commit()

        if not count:
            error = QMessageBox()
            error.setWindowTitle('error')
            error.setText('Логин не зарегистрирован. \n'
                          'Нажмите "Новый пользователь",   \n'
                          'что бы зарегистрировать под текущим логином \n'
                          'или введите корректный логин')
            error.exec_()
        elif count[0] == user_login and count[1] != user_password:
            error = QMessageBox()
            error.setWindowTitle('error')
            error.setText('Неверный пароль. \n'
                          'Попробуйте ввести снова!')
            error.exec_()
        else:  # Открытие главного окна
            if self.checkBox.checkState() == 2:
                self.sql.execute('''UPDATE users SET state = 0''')
                self.sql.execute('''UPDATE users SET state = 2 WHERE login=?''', (user_login,))
                self.db.commit()
            self.user = self.sql.execute('''SELECT rowid FROM users WHERE login=?''', (user_login,)).fetchall()
            self.deadliner = Deadliner(self.user)
            self.deadliner.show()
            self.hide()

    def RegProcess(self, loginEdit, passwordEdit):
        user_login = loginEdit
        user_password = passwordEdit
        if not user_login or not user_password:
            msg = QMessageBox.information(
                self,
                'error',
                'Ошибка. Введите логин и пароль для успешной регистрации'
            )
            return

        self.sql.execute("SELECT login FROM users WHERE login = ?", (user_login,))

        if self.sql.fetchone() is None:
            self.sql.execute('''UPDATE users SET state = 0''')
            self.sql.execute(
                "INSERT INTO users (login, password, state) VALUES (?,?,?)",
                (user_login, user_password, str(self.checkBox.checkState()))
            )
            self.db.commit()
            print('Регистрация успешна')
            msg = QMessageBox.information(
                self,
                'Успех',
                'Вы успешно зарегистрировались. \n'
                'Нажмите "Вход".'
            )
        else:
            print('Login are register already')
            msg = QMessageBox.information(
                self,
                'error',
                'Такой логин уже существует.'
            )
            return

        self.db.commit()

    def exit_log(self):
        self.db.close()
        self.close()


def except_hook(cls, exception, traceback):
    sys.excepthook(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LogIN()
    ex.show()
    # Ловим и показываем ошибки PyQt5 в терминале:
    sys.excepthook = except_hook
    sys.exit(app.exec_())
