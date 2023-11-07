from random import randint
import sys
import sqlite3
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QLabel, QDialog, QLineEdit, QRadioButton, QButtonGroup, QCheckBox
from PyQt5.QtGui import QPixmap, QImage


class TestTask:
    def __init__(self, text, answer_type, possible_answers, true_answers, tag,
                 picture=None):  # текст задания(str), тип ответа на вопрос(int), #возможные ответы([str, str...str],
        # ответы на вопрос([str, str...str]), тэг(str), наличие картинки(None/BLOB)

        self.text = text
        self.answer_type = answer_type
        self.possible_answers = possible_answers
        self.true_answers = true_answers
        self.tag = tag
        self.picture = picture

    def get_text(self):
        return self.text

    def set_text(self, new_text):
        self.text = new_text

    def get_answer_type(self):
        return self.answer_type

    def set_answer_type(self, new_answer_type):
        self.answer_type = new_answer_type

    def get_possible_answers(self):
        return self.possible_answers

    def set_possible_answers(self, new_possible_answers):
        self.possible_answers = new_possible_answers

    def get_true_answers(self):
        return self.true_answers

    def set_true_answers(self, new_true_answers):
        self.true_answers = new_true_answers

    def get_tag(self):
        return self.tag

    def set_tag(self, new_tag):
        self.tag = new_tag

    def get_picture(self):
        return self.picture

    def set_picture(self, new_picture):
        self.picture = new_picture


def transform_to_picture(blob, filename):
    with open(filename, "wb") as file:
        file.write(blob)
    file.close()
    return filename


def transform_to_blob(filename):
    with open(filename, "rb") as file:
        blob = file.read()
    return blob


class Authorization(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("authorization.ui", self)

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
        uic.loadUi("registration.ui", self)
        self.goBackButton.clicked.connect(self.return_to_auth)
        self.createAccountButton.clicked.connect(self.create_new_account)

    def return_to_auth(self):
        reg.hide()
        auth.show()

    def create_new_account(self):
        cur = con.cursor()

        try:
            if "@" not in self.usernameEdit.text() and "." not in self.usernameEdit.text() and\
                    len(self.usernameEdit.text()) > 5:
                self.statusBar().showMessage("Ошибка! Неверно указана электронная почта!")

            elif len(self.passwordEdit.text()) < 8:
                self.statusBar().showMessage("Ошибка! пароль должен содержать минимум 8 символов!")

            elif self.passwordEdit.text() != self.confirmEdit.text():
                self.statusBar().showMessage("Ошибка! Не совпадают пароли!")

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
            self.statusBar().showMessage("Ошибка! Укажите ФИО!")


class Task(QWidget):
    def __init__(self, num):
        super().__init__()
        uic.loadUi("randomtask.ui", self)

        cur = con.cursor()

        self.max_id = int(cur.execute('''SELECT MAX(id) FROM tasks''').fetchone()[0])
        self.actual_id = num
        self.init_args = cur.execute(f'''SELECT * FROM tasks WHERE id = {self.actual_id}''').fetchone()
        self.random_num = randint(1, self.max_id)

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
            self.answerButton.move(260, 560)

            coords = 240

            for text in self.possible_answers:
                btn = QRadioButton(f"{text}", self)
                btn.setGeometry(20, coords, 661, 61)
                self.btngroup.addButton(btn)
                coords += 70

        elif self.answer_type == 3:
            self.check_boxes = list()
            self.answerButton.move(260, 560)

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

        self.answerButton.clicked.connect(self.check_answer)

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
        uic.loadUi("task.ui", self)
        self.answerButton.setGeometry(420, 550, 231, 31)
        self.setWindowTitle("Пробный экзамен")

        self.position = 0
        self.checked_result = list()
        self.flag = False

        self.nextButton.clicked.connect(self.next_task)
        self.PreviousButton.clicked.connect(self.previous_task)

    def next_task(self):
        self.position += 1
        self.flag = True

    def previous_task(self):
        self.position -= 1

    def get_position(self):
        return self.position

    def set_position(self, new_pos):
        self.position = new_pos

    def get_result(self):
        return self.checked_result + self.answers

    def check_answer(self):
        try:
            if self.answer_type == 1:

                if self.answerEdit.text() in self.answers:
                    self.checked_result = [self.actual_id, "Верно"]
                else:
                    self.checked_result = [self.actual_id, "Неверно"]

            elif self.answer_type == 2:

                if self.btngroup.checkedButton().text() in self.answers:
                    self.checked_result = [self.actual_id, "Верно"]
                else:
                    self.checked_result = [self.actual_id, "Неверно"]

            elif self.answer_type == 3:
                counter = 0

                for x in self.check_boxes:
                    if x.isChecked():
                        counter += 1

                if counter == len(self.answers):
                    self.checked_result = [self.actual_id, "Верно"]
                elif counter == 0:
                    self.checked_result = [self.actual_id, "Неверно"]
                else:
                    self.checked_result = [self.actual_id, "Частично верно"]

        except AttributeError:
            pass


class Result(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("randomtaskresult.ui", self)


class MainProgram(QMainWindow):
    def __init__(self):
        super(MainProgram, self).__init__()
        uic.loadUi("mainwindow.ui", self)

        self.RandomTaskButton.clicked.connect(self.get_random_task)
        self.searchButton.clicked.connect(self.search_task)
        self.thirdCategoryButton.clicked.connect(self.generate_exam)
        self.secondCategoryButton.clicked.connect(self.generate_exam)
        self.firstCategoryButton.clicked.connect(self.generate_exam)

    def get_random_task(self):
        try:
            cur = con.cursor()
            id_max = cur.execute(f'''SELECT MAX(id) FROM tasks''').fetchone()[0]
            self.rd = Task(randint(1, id_max))
            self.rd.show()
            cur.close()
        except Exception as e:
            print(e)

    def search_task(self):
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

    def generate_exam(
            self):  # TODO до 10го ноября придумать как реализовать, иначе искоренить
        if self.examsGroup.sender().text() == "III" or self.examsGroup.sender().text() == "II" \
                or self.examsGroup.sender().text() == "I":
            res = Result()
            res.resultLabel.setText("Функция в разработке ;)))))")
            res.exec()

            # cur = con.cursor()
            # id_max = cur.execute('''SELECT MAX(id) FROM tasks''').fetchone()[0]
            # exam_tasks_id = [randint(1, id_max) for _ in range(5)]

    def closeEvent(self, event):
        con.close()


if __name__ == '__main__':
    con = sqlite3.connect("test_bd.sqlite")
    app = QApplication(sys.argv)
    auth = Authorization()
    auth.show()
    reg = Registration()
    prog = MainProgram()
    sys.exit(app.exec_())
