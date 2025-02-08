from random import randint, shuffle, choice
import sys
import sqlite3
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QLabel, QDialog, QLineEdit, QRadioButton, QButtonGroup, QCheckBox, QPushButton, QVBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap, QImage

is_mod = False


def transform_to_picture(blob, filename):
    with open(filename, "wb") as file:
        file.write(blob)
    file.close()
    return filename


def transform_to_blob(filename):
    with open(filename, "rb") as file:
        blob = file.read()
    return blob


class WrongIdError(Exception):
    pass


class NoTextError(Exception):
    pass


class NoAnswerTypeError(Exception):
    pass


class NoPossibleAnswersError(Exception):
    pass


class WrongAnswerTypeError(Exception):
    pass


class NoRightAnswersError(Exception):
    pass


class Authorization(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/authorization.ui", self)

        self.authorizationButton.clicked.connect(self.authorize)
        self.registrationButton.clicked.connect(self.switch_to_registration)

    def switch_to_registration(self):
        auth.hide()
        reg.show()

    def authorize(self):
        try:
            cur = con.cursor()
            check_pass = cur.execute(f'''SELECT password FROM accounts 
            WHERE username = "{self.usernameEdit.text()}"''').fetchone()[0]

            if check_pass == self.passwordEdit.text():
                self.statusBar().showMessage("Подключено!!!")
                status = eval(cur.execute(f'''SELECT is_moderator FROM accounts WHERE username
                 = "{self.usernameEdit.text()}"''').fetchone()[0])
                global is_mod
                is_mod = status
                cur.close()
                auth.close()
                reg.close()
                prog.show()
            else:
                self.statusBar().showMessage("Неправильный логин или пароль")

        except TypeError:
            self.statusBar().showMessage("Неправильный логин или пароль")


class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/registration.ui", self)
        self.goBackButton.clicked.connect(self.return_to_auth)
        self.createAccountButton.clicked.connect(self.create_new_account)

    def return_to_auth(self):
        reg.hide()
        auth.show()

    def create_new_account(self):
        cur = con.cursor()

        try:
            if "@" not in self.usernameEdit.text() and "." not in self.usernameEdit.text() and \
                    len(self.usernameEdit.text()) > 5:
                self.statusBar().showMessage("Ошибка! Неверно указана электронная почта!")

            elif len(self.passwordEdit.text()) < 8:
                self.statusBar().showMessage("Ошибка! пароль должен содержать минимум 8 символов!")

            elif self.passwordEdit.text() != self.confirmEdit.text():
                self.statusBar().showMessage("Ошибка! Не совпадают пароли!")

            elif len(self.nameEdit.text()) < 2 and len(self.surnameEdit.text()) < 1 and len(self.otchestvoEdit) < 4:
                self.statusBar().showMessage("Укажите верное ФИО!")

            else:
                cur.execute(f'''INSERT INTO accounts(username, name, surname, otchestvo, password, is_moderator)
                 VALUES ("{self.usernameEdit.text()}", "{self.nameEdit.text()}",
                "{self.surnameEdit.text()}", 
                "{self.otchestvoEdit.text()}", "{self.passwordEdit.text()}", "False")''')

                con.commit()
                cur.close()

                self.statusBar().showMessage("Аккаунт создан успешно!")

                prog.show()
                reg.close()
                auth.close()

        except sqlite3.Error:
            self.statusBar().showMessage("Указанная почта уже занята!")


class Task(QWidget):
    def __init__(self, num, close_on_right_answer=True):
        super().__init__()
        uic.loadUi("ui/randomtask.ui", self)
        self.answerButton = QPushButton("ответить", self)
        self.answerButton.setGeometry(450, 550, 201, 31)
        self.answerButton.clicked.connect(self.check_answer)
        layout = QVBoxLayout()
        self.setLayout(layout)

        cur = con.cursor()

        self.max_id = int(cur.execute('''SELECT MAX(id) FROM tasks''').fetchone()[0])
        self.actual_id = num
        self.init_args = cur.execute(f'''SELECT * FROM tasks WHERE id = {self.actual_id}''').fetchone()
        self.random_num = randint(1, self.max_id)
        self.close_on_right_answer = close_on_right_answer

        cur.close()

        self.setWindowTitle(f"Вопрос № {self.actual_id}")
        self.TextLabel.setText(f"{self.init_args[1]}")
        self.answer_type = int(self.init_args[2])
        self.possible_answers = eval(self.init_args[3])
        self.answers = eval(self.init_args[4])
        self.picture = eval(self.init_args[6])

        if self.answer_type == 1:

            self.answerEdit = QLineEdit(self)
            self.answerEdit.setGeometry(60, 280, 591, 20)

        elif self.answer_type == 2:

            self.btngroup = QButtonGroup(self)

            coords = 240

            for text in self.possible_answers:
                btn = QRadioButton(f"{text}", self)
                btn.setGeometry(20, coords, 661, 61)
                self.btngroup.addButton(btn)
                coords += 70

        elif self.answer_type == 3:
            self.check_boxes = list()

            coords_1 = 250
            for text in self.possible_answers:
                check_box = QCheckBox(f"{text}", self)
                check_box.setGeometry(10, coords_1, 681, 20)
                self.check_boxes.append(check_box)
                coords_1 += 40

        if self.picture is None:
            pass
        else:
            self.ImageLabel = QLabel()
            self.horizontalLayout.addWidget(self.ImageLabel)

            self.image = QImage(transform_to_picture(self.picture, "rdpicture.jpg"))
            self.pixmap = QPixmap.fromImage(self.image)
            self.ImageLabel.setPixmap(self.pixmap)
            self.ImageLabel.setWordWrap(True)
            self.ImageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def check_answer(self):
        mistakes = {1: "памятку для линейных судей по танцу.",
                    2: "памятку для технических судей.",
                    3: "памятку для главных судей.",
                    4: "памятку для секретарей.",
                    5: "памятку для главных секретарей.",
                    6: "памятку для линейных судей по акробатике."}
        try:
            if self.answer_type == 1:
                if self.answerEdit.text() in self.answers:
                    res = Result()
                    res.exec()
                    if self.close_on_right_answer:
                        self.close()
                else:
                    cur = con.cursor()
                    tag = cur.execute(f'''SELECT tag FROM tasks WHERE id = {self.actual_id}''').fetchone()[0]
                    cur.close()

                    res = Result()
                    res.resultLabel.setText(f"Неправильно! см. {mistakes[tag]}")
                    res.exec()
                    self.answerEdit.clear()

            elif self.answer_type == 2:
                if self.btngroup.checkedButton().text() in self.answers:
                    res = Result()
                    res.exec()
                    if self.close_on_right_answer:
                        self.close()

                else:
                    cur = con.cursor()
                    tag = cur.execute(f'''SELECT tag FROM tasks WHERE id = {self.actual_id}''').fetchone()[0]
                    cur.close()

                    res = Result()
                    res.resultLabel.setText(f"Неправильно! см. {mistakes[tag]}")
                    res.exec()

            elif self.answer_type == 3:
                counter = 0
                for x in self.check_boxes:
                    if x.isChecked():
                        counter += 1
                if counter == 0:
                    cur = con.cursor()
                    tag = cur.execute(f'''SELECT tag FROM tasks WHERE id = {self.actual_id}''').fetchone()[0]
                    cur.close()

                    res = Result()
                    res.resultLabel.setText(f"Неправильно! см. {mistakes[tag]}")
                    res.exec()

                elif counter != len(self.answers):
                    cur = con.cursor()
                    tag = cur.execute(f'''SELECT tag FROM tasks WHERE id = {self.actual_id}''').fetchone()[0]
                    cur.close()

                    res = Result()
                    res.resultLabel.setText(f"Частично правильно. см. {mistakes[tag]}")
                    res.exec()

                else:
                    res = Result()
                    res.exec()
                    if self.close_on_right_answer:
                        self.close()

        except AttributeError:
            cur = con.cursor()
            tag = cur.execute(f'''SELECT tag FROM tasks WHERE id = {self.actual_id}''').fetchone()[0]
            cur.close()

            res = Result()
            res.resultLabel.setText(f"Неправильно! см. {mistakes[tag]}")
            res.exec()


class ExamTask(Task):
    def __init__(self, num):
        super().__init__(num)
        self.answerButton.close()

    def get_answer(self):
        if self.answer_type == 1:
            if len(self.answerEdit.text()) > 0:
                return self.answerEdit.text(), self.answers
            else:
                return "Нет ответа", self.answers

        elif self.answer_type == 2:
            try:
                if len(self.btngroup.checkedButton().text()) > 0:
                    return self.btngroup.checkedButton().text(), self.answers
                else:
                    return "Нет ответа", self.answers
            except AttributeError:
                return "Нет ответа", self.answers

        elif self.answer_type == 3:
            user_inputs = list()

            for x in self.check_boxes:
                if x.isChecked():
                    user_inputs.append(x.text())

            if len(user_inputs) > 0:
                return user_inputs, self.answers
            else:
                return "Нет ответа", self.answers


class ExamResult(QDialog):
    def __init__(self, answers_list):
        super().__init__()
        uic.loadUi("ui/examresult.ui", self)
        self.answers_list = answers_list
        self.flag = False
        self.yesButton.clicked.connect(self.calculate)
        self.noButton.clicked.connect(self.close)

    def calculate(self):
        self.close()
        self.flag = True
        res = ExamResultStatus(self.answers_list)
        res.exec()


class ExamResultStatus(QDialog):
    def __init__(self, answers_list):
        super().__init__()
        uic.loadUi("ui/examresultstatus.ui", self)
        counter = 0

        for x in answers_list:
            if x[0] in x[1]:
                counter += 1

        percentage = counter / len(answers_list) * 100
        self.rightanswerslabel.setText(f"Ваш результат {counter} из {len(answers_list)} ({percentage}%)")

        if percentage >= 60:
            self.statuslabel.setText("Поздравляем! Вы успешно завершили пробный экзамен!")
        else:
            self.statuslabel.setText("К сожалению, вы не завершили тест, вы всегда можете попробовать снова!")


class Exam(QMainWindow):
    def __init__(self, category):
        super().__init__()
        uic.loadUi("ui/examwindow.ui", self)

        cur = con.cursor()
        max_id = cur.execute('''SELECT MAX(id) from tasks''').fetchone()[0]
        cur.close()

        if self.stackedWidget.currentIndex() == 1:
            self.previous_Button.setEnabled(False)
        else:
            self.previous_Button.setEnabled(True)

        temp = [x for x in range(1, max_id + 1)]
        shuffle(temp)
        ids_list = temp[:15]

        if category == "I":
            self.task = ExamTask(ids_list[0])
            self.task1 = ExamTask(ids_list[1])
            self.task2 = ExamTask(ids_list[2])
            self.task3 = ExamTask(ids_list[3])
            self.task4 = ExamTask(ids_list[4])
            self.task5 = ExamTask(ids_list[5])
            self.task6 = ExamTask(ids_list[6])
            self.task7 = ExamTask(ids_list[7])
            self.task8 = ExamTask(ids_list[8])
            self.task9 = ExamTask(ids_list[9])
            self.task10 = ExamTask(ids_list[10])
            self.task11 = ExamTask(ids_list[11])
            self.task12 = ExamTask(ids_list[12])
            self.task13 = ExamTask(ids_list[13])
            self.task14 = ExamTask(ids_list[14])

            self.tasks = [self.task, self.task1, self.task2, self.task3, self.task4,
                          self.task5, self.task6, self.task7, self.task8, self.task9,
                          self.task10, self.task11, self.task12, self.task13, self.task14]
        elif category == "II":
            self.task = ExamTask(ids_list[0])
            self.task1 = ExamTask(ids_list[1])
            self.task2 = ExamTask(ids_list[2])
            self.task3 = ExamTask(ids_list[3])
            self.task4 = ExamTask(ids_list[4])
            self.task5 = ExamTask(ids_list[5])
            self.task6 = ExamTask(ids_list[6])
            self.task7 = ExamTask(ids_list[7])
            self.task8 = ExamTask(ids_list[8])
            self.task9 = ExamTask(ids_list[9])

            self.tasks = [self.task, self.task1, self.task2, self.task3, self.task4,
                          self.task5, self.task6, self.task7, self.task8, self.task9]
        elif category == "III":
            self.task = ExamTask(ids_list[0])
            self.task1 = ExamTask(ids_list[1])
            self.task2 = ExamTask(ids_list[2])
            self.task3 = ExamTask(ids_list[3])
            self.task4 = ExamTask(ids_list[4])

            self.tasks = [self.task, self.task1, self.task2, self.task3, self.task4]

        for x in self.tasks:
            self.stackedWidget.addWidget(x)
            self.stackedWidget.setCurrentWidget(self.tasks[0])

        self.counterLabel.setText(f'Задание {self.stackedWidget.currentIndex() - 1} из {len(self.tasks)}')
        self.next_Button.clicked.connect(self.next_task)
        self.previous_Button.clicked.connect(self.previous_task)
        self.saveAnswerButton.clicked.connect(self.save_answers)

    def next_task(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() + 1)

        if self.stackedWidget.currentIndex() == len(self.tasks) + 1:
            self.next_Button.setEnabled(False)
        else:
            self.next_Button.setEnabled(True)

        if self.stackedWidget.currentIndex() == 2:
            self.previous_Button.setEnabled(False)
        else:
            self.previous_Button.setEnabled(True)

        self.counterLabel.setText(f'Задание {self.stackedWidget.currentIndex() - 1} из {len(self.tasks)}')

    def previous_task(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 1)

        if self.stackedWidget.currentIndex() == 2:
            self.previous_Button.setEnabled(False)
        else:
            self.previous_Button.setEnabled(True)

        if self.stackedWidget.currentIndex() == len(self.tasks) + 1:
            self.next_Button.setEnabled(False)
        else:
            self.next_Button.setEnabled(True)

        self.counterLabel.setText(f'Задание {self.stackedWidget.currentIndex() - 1} из {len(self.tasks)}')

    def save_answers(self):
        results = list()
        for x in self.tasks:
            temp = x.get_answer()
            results.append(temp)
        res = ExamResult(results)
        res.exec()

        if res.flag:
            self.close()


class Result(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/randomtaskresult.ui", self)


class TaskRedactorManual(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/taskcreatormanual.ui", self)

        self.okButton.clicked.connect(self.close)
        self.already_read.stateChanged.connect(self.check_config)

    def check_config(self):
        if self.already_read.isChecked():
            with open("config/config.txt", mode="r+", encoding="utf-8") as f:
                config = "".join([line.replace("task_creator_manual_read = 0", "task_creator_manual_read = 1")
                                  for line in f.readlines()])
                f.seek(0)
                f.write(config)
                f.close()
        else:
            with open("config/config.txt", mode="r+", encoding="utf-8") as f:
                config = "".join([line.replace("task_creator_manual_read = 1", "task_creator_manual_read = 0")
                                  for line in f.readlines()])
                f.seek(0)
                f.write(config)
                f.close()


class TaskRedactor(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/taskcreator.ui", self)
        self.type_answer_buttons = [self.lineanswerButton, self.oneanswerButton, self.multipleanswerButton]
        self.buttonGroup.setId(self.lineanswerButton, 0)
        self.buttonGroup.setId(self.oneanswerButton, 1)
        self.buttonGroup.setId(self.multipleanswerButton, 2)

        self.get_infoButton.clicked.connect(self.get_info)
        self.createtaskButton.clicked.connect(self.create_task)
        self.choosefileButton.clicked.connect(self.get_file)
        self.clearFileButton.clicked.connect(self.clear_file)

    def get_info(self):
        self.statusBar().clearMessage()
        self.imagePreview.clear()

        try:
            cur = con.cursor()
            task_args = cur.execute(f'''SELECT * FROM tasks WHERE id = {self.idEdit.text()}''').fetchall()[0]
            cur.close()

            self.taskTextEdit.setText(task_args[1])
            self.buttonGroup.buttons()[task_args[2] - 1].setChecked(True)

            if eval(task_args[3]) is None:
                pass
            else:
                self.possibleanswersEdit.setText("; ".join(eval(task_args[3])))

            self.rightanswersedit.setText("; ".join(eval(task_args[4])))
            self.tagEdit.setText(str(task_args[5]))

            if eval(task_args[6]) is None:
                pass
            else:
                image = QImage(transform_to_picture(eval(task_args[6]), "preview_picture.jpg"))
                pixmap = QPixmap.fromImage(image)
                self.imagePreview.setPixmap(pixmap)
                self.imagePreview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        except IndexError:
            self.statusBar().showMessage("Задания с таким номером нет,"
                                         " если хотите создать новое не вводите ничего в поле с id")
            self.taskTextEdit.setText("Вводить сюда...")
            self.possibleanswersEdit.clear()
            self.rightanswersedit.clear()
            self.imagePreview.clear()

        except sqlite3.Error:
            self.statusBar().showMessage("Неправильно введен id")
            self.taskTextEdit.setText("Вводить сюда...")
            self.possibleanswersEdit.clear()
            self.rightanswersedit.clear()
            self.imagePreview.clear()

    def get_file(self):
        self.filename = QFileDialog.getOpenFileName(self, "Выберите картинку 250 на 220 пикселей",
                                                    "", "Картинки (*.jpg)")[0]
        self.image = QImage(self.filename)
        x, y = self.image.size().width(), self.image.size().height()
        if x > 250 and y > 220:
            self.statusBar().showMessage("Неправильное разрешение картинки! (максимум 250 x 220 пикселей)")
        else:
            pixmap = QPixmap.fromImage(self.image)
            self.imagePreview.setPixmap(pixmap)
            self.imagePreview.setWordWrap(True)
            self.imagePreview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.statusBar().clearMessage()

    def create_task(self):
        new_task_args = list()
        flag = False
        try:
            if len(self.tagEdit.text()) == 0:
                new_task_args.clear()
                raise WrongIdError("Введен неверный тэг!")
            elif int(self.tagEdit.text()) > 6:
                new_task_args.clear()
                raise WrongIdError("Введен неверный тэг!")
            elif int(self.tagEdit.text()) == 0:
                new_task_args.clear()
                raise WrongIdError("Введен неверный тэг!")
            else:
                new_task_args.append(int(self.tagEdit.text()))

            if self.taskTextEdit.toPlainText() == "Вводить сюда...":
                new_task_args.clear()
                raise NoTextError("Введите текст задания!")
            else:
                new_task_args.append(self.taskTextEdit.toPlainText())

            if self.buttonGroup.checkedButton() is None:
                new_task_args.clear()
                raise NoAnswerTypeError("Выберете тип ответа!")
            else:
                if self.buttonGroup.checkedId() == 0:
                    new_task_args.append(self.buttonGroup.checkedId() + 1)
                    flag = True
                else:
                    new_task_args.append(self.buttonGroup.checkedId() + 1)
                    flag = False

            if len(self.possibleanswersEdit.text()) == 0 and not flag:
                new_task_args.clear()
                raise NoPossibleAnswersError("Введите возможные ответы!")
            elif self.buttonGroup.checkedId() == 0 and len(self.possibleanswersEdit.text()) > 0:
                new_task_args.clear()
                raise WrongAnswerTypeError("Для этого типа ответа недоступны возможные ответы!")
            else:
                if len(self.possibleanswersEdit.text()) == 0:
                    new_task_args.append("None")
                else:
                    new_task_args.append(self.possibleanswersEdit.text().split("; "))

            if len(self.rightanswersedit.text()) == 0:
                new_task_args.clear()
                raise NoRightAnswersError("Введите правильные ответы")
            else:
                new_task_args.append(self.rightanswersedit.text().split("; "))

            if self.imagePreview.pixmap() is None:
                new_task_args.append("None")
            else:
                temp_pixmap = self.imagePreview.pixmap()
                temp_image = temp_pixmap.toImage()
                temp_image.save("temp_pic.jpg")
                new_task_args.append(transform_to_blob("temp_pic.jpg"))

        except Exception as e:
            self.statusBar().showMessage(f"Ошибка: {e}")

        else:
            try:
                if len(self.idEdit.text()) == 0:
                    cur = con.cursor()

                    query = '''INSERT INTO tasks(text, answer_type, possible_answers,
                     true_answers, tag, picture) VALUES(?, ?, ?, ?, ?, ?)'''
                    data = (new_task_args[1], new_task_args[2], str(new_task_args[3]),
                            str(new_task_args[4]), new_task_args[0], str(new_task_args[5]))
                    cur.execute(query, data)
                    con.commit()
                    new_id = cur.execute('''SELECT MAX(id) FROM tasks''').fetchone()[0]

                    cur.close()

                    self.statusBar().showMessage(f"Задание создано с номером {new_id}")
                else:
                    cur = con.cursor()

                    query = f'''UPDATE tasks SET text = ?, answer_type = ?, 
                    possible_answers = ?, true_answers = ?, 
                    tag = ?, picture = ?
                    WHERE id = {int(self.idEdit.text())}'''
                    data = (new_task_args[1], new_task_args[2], str(new_task_args[3]),
                            str(new_task_args[4]), new_task_args[0], str(new_task_args[5]))
                    cur.execute(query, data)

                    con.commit()
                    cur.close()

                    self.statusBar().showMessage(f"Задание с номером {self.idEdit.text()} обновлено")

            except Exception as e:
                self.statusBar().showMessage(f"Неожиданная ошибка :{e}")

    def clear_file(self):
        self.imagePreview.clear()


class CategoryTasks(QMainWindow):
    def __init__(self, task_ids):
        super().__init__()
        uic.loadUi("ui/categorytasks.ui", self)

        self.task_ids = task_ids

        for x in task_ids:
            self.stackedWidget.addWidget(Task(x, close_on_right_answer=False))

        self.next_Button.clicked.connect(self.next_task)
        self.previous_Button.clicked.connect(self.previous_task)

        self.stackedWidget.setCurrentIndex(2)
        self.previous_Button.setEnabled(False)
        if self.stackedWidget.currentIndex() == 2:
            self.previous_Button.setEnabled(False)
        if self.stackedWidget.currentIndex() - 1 == len(self.task_ids):
            self.next_Button.setEnabled(False)

        self.counterLabel.setText(f"Задание {self.stackedWidget.currentIndex() - 1} из {len(self.task_ids)}")

    def next_task(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() + 1)

        if self.stackedWidget.currentIndex() == 2:
            self.previous_Button.setEnabled(False)
        else:
            self.previous_Button.setEnabled(True)

        if self.stackedWidget.currentIndex() - 1 == len(self.task_ids):
            self.next_Button.setEnabled(False)
        else:
            self.next_Button.setEnabled(True)

        self.counterLabel.setText(f"Задание {self.stackedWidget.currentIndex() - 1} из {len(self.task_ids)}")

    def previous_task(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 1)

        if self.stackedWidget.currentIndex() == 2:
            self.previous_Button.setEnabled(False)
        else:
            self.previous_Button.setEnabled(True)

        if self.stackedWidget.currentIndex() - 1 == len(self.task_ids):
            self.next_Button.setEnabled(False)
        else:
            self.next_Button.setEnabled(True)

        self.counterLabel.setText(f"Задание {self.stackedWidget.currentIndex() - 1} из {len(self.task_ids)}")


class NoAccess(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/access_denied.ui", self)


class TestCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/testcreator.ui", self)
        self.pushButton.clicked.connect(self.create_test)

    def create_test(self):
        input_ids = list(map(int, self.lineEdit.text().split("; ")))

        cur = con.cursor()
        temp = cur.execute('''SELECT id FROM tasks''').fetchall()
        cur.close()

        all_ids = [x[0] for x in temp]

        counter = 0
        for x in input_ids:
            if x in all_ids:
                counter += 1
            else:
                self.statusBar().showMessage(f"Ошибка, задания с номером {x} не существует")
                counter = 0

        if counter == len(input_ids):
            cur = con.cursor()
            cur.execute(f'''INSERT INTO custom_tests(ids_list) VALUES ("{input_ids}")''')
            con.commit()
            new_id = cur.execute(f'''SELECT MAX(id) FROM custom_tests''').fetchone()[0]
            cur.close()
            self.statusBar().showMessage(f"Тест создан с номером {new_id}")


class TestCreatorManual(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("testcreatormanual.ui", self)

        self.already_read.stateChanged.connect(self.check_config)
        self.okButton.clicked.connect(self.close)

    def check_config(self):
        if self.already_read.isChecked():
            with open("config/config.txt", mode="r+", encoding="utf-8") as f:
                config = "".join([line.replace("test_creator_manual_read = 0", "test_creator_manual_read = 1")
                                  for line in f.readlines()])
                f.seek(0)
                f.write(config)
                f.close()
        else:
            with open("config/config.txt", mode="r+", encoding="utf-8") as f:
                config = "".join([line.replace("test_creator_manual_read = 1", "test_creator_manual_read = 0")
                                  for line in f.readlines()])
                f.seek(0)
                f.write(config)
                f.close()


class Xd(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/xd.ui", self)


class MainProgram(QMainWindow):
    def __init__(self):
        super(MainProgram, self).__init__()
        uic.loadUi("ui/mainwindow.ui", self)

        self.RandomTaskButton.clicked.connect(self.get_random_task)
        self.searchButton.clicked.connect(self.search_task)
        self.thirdCategoryButton.clicked.connect(self.generate_exam)
        self.secondCategoryButton.clicked.connect(self.generate_exam)
        self.firstCategoryButton.clicked.connect(self.generate_exam)
        self.taskcreatorButton.clicked.connect(self.open_task_redactor)
        self.testCreatorButton.clicked.connect(self.open_test_creator)
        self.searchButton_2.clicked.connect(self.search_test)
        self.category_1.clicked.connect(self.category_show)
        self.category_2.clicked.connect(self.category_show)
        self.category_3.clicked.connect(self.category_show)
        self.category_4.clicked.connect(self.category_show)
        self.category_5.clicked.connect(self.category_show)
        self.category_6.clicked.connect(self.category_show)

    def get_random_task(self):
        try:
            cur = con.cursor()
            # id_max = cur.execute(f'''SELECT MAX(id) FROM tasks''').fetchone()[0]
            temp = cur.execute('''SELECT id FROM tasks''').fetchall()
            possible_ids = [x[0] for x in temp]

            self.rd = Task(choice(possible_ids))
            self.rd.show()
            cur.close()
        except Exception as e:
            self.statusBar().showMessage(f"Неожиданная ошибка: {e}")

    def search_task(self):
        self.statusBar().clearMessage()
        cur = con.cursor()
        try:
            self.task = Task(int(self.searchEdit.text()))
            self.task.show()
            self.statusBar().clearMessage()
        except ValueError:
            self.statusBar().showMessage("Задание с таким номером не существует!")
        except TypeError:
            self.statusBar().showMessage("Задание с таким номером не существует!")
        cur.close()

    def search_test(self):
        self.statusBar().clearMessage()
        cur = con.cursor()
        try:
            ids = eval(cur.execute(f'''SELECT ids_list FROM custom_tests
             WHERE id = {int(self.lineEdit_2.text())}''').fetchone()[0])
            cur.close()
            self.customtest = CategoryTasks(ids)
            self.customtest.setWindowTitle(f"Кастомный тест № {self.lineEdit_2.text()}")
            self.customtest.show()
        except ValueError:
            self.statusBar().showMessage("Ошибка! Теста с таким номером не сущетсвует")
        except TypeError:
            self.statusBar().showMessage("Ошибка! Теста с таким номером не сущетсвует")

    def generate_exam(self):
        self.exam = Exam(self.examsGroup.sender().text())
        self.exam.show()

    def open_task_redactor(self):
        global is_mod
        if is_mod:
            try:
                self.redactor = TaskRedactor()
                self.redactor.show()

                with open("config/config.txt", mode="r", encoding="utf-8") as f:
                    lines = [x.rstrip('\n') for x in f]
                    f.close()
                if lines[0] == 'task_creator_manual_read = 0':
                    self.manual_1 = TaskRedactorManual()
                    self.manual_1.show()
                else:
                    pass
            except Exception as e:
                self.statusBar().showMessage(f"Неожиданная ошибка: {e}")
        else:
            self.no_acces = NoAccess()
            self.no_acces.show()

    def open_test_creator(self):
        global is_mod
        if is_mod:
            self.tcreator = TestCreator()
            self.tcreator.show()

            with open("config/config.txt", mode="r", encoding="utf-8") as f:
                lines = [x.rstrip('\n') for x in f]
                f.close()
            if lines[1] == "test_creator_manual_read = 0":
                self.manual_2 = TestCreatorManual()
                self.manual_2.show()
            else:
                pass
        else:
            self.no_acces = NoAccess()
            self.no_acces.show()

    def category_show(self):
        d = {"Линейный судья": 1,
             "Технический судья": 2,
             "Главный судья": 3,
             "Секретарь": 4,
             "Главный секретарь": 5,
             "Акробатика": 6}
        task_tag = self.tasksgroup.sender().text()
        cur = con.cursor()
        temp = cur.execute(f'''SELECT id FROM tasks WHERE tag = {d[task_tag]}''').fetchall()
        cur.close()

        if len(temp) == 0:
            self.xd = Xd()
            self.xd.show()
            self.xd.setWindowTitle(f"Задания с категорией: {self.tasksgroup.sender().text()}")
        else:
            tagged_ids = [x[0] for x in temp]
            self.categorytasks = CategoryTasks(tagged_ids)
            self.categorytasks.show()
            self.categorytasks.setWindowTitle(f"Задания с категорией: {self.tasksgroup.sender().text()}")

    def closeEvent(self, event):
        con.close()


if __name__ == '__main__':
    con = sqlite3.connect("database/test_bd.sqlite")
    app = QApplication(sys.argv)
    auth = Authorization()
    auth.show()
    reg = Registration()
    prog = MainProgram()
    sys.exit(app.exec_())
