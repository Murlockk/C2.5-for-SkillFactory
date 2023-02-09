import time
from random import randint


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):   # Возможность сравнивать объекты. Точки с равными координатами теперь сравнимы
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"({self.x}, {self.y})"


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "The selected field is outside the battle zone!"  # "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "The field is occupied"  # "Это поле занято!"


class BoardWrongShipException(BoardException):
    pass


class Ship:
    def __init__(self, bow, dimension, o):
        self.dimension = dimension   # Длина корабля
        self.bow = bow               # Координаты носа корабля (2)
        self.o = o                   # Ориентация корабля
        self.lives = dimension       # Количество 'жизней' корабля

    @property           # Свойство используемое при генерации кораблей
    def dots(self):
        ship_dots = []  # Складирует точки кораблей в зависимости от их ориентации и размера
        for i in range(self.dimension):
            cur_x = self.bow.x
            cur_y = self.bow.y
            if self.o == 0:
                cur_x += i
            elif self.o == 1:
                cur_y += i
            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots

    def shot_in_dots(self, shot):
        return shot in self.dots


# Блок игрового поля
class Board:
    def __init__(self, hid=False, size=6):
        self.size = size  # Размер доски
        self.hid = hid    # Скрыть или показать корабль противника.
        self.count = 0    # Счетчик уничтоженных кораблей
        self.field = [["O"] * size for _ in range(size)]
        self.busy = []    # Хранятся занятые точки
        self.ships = []   # Список точек кораблей на доске

    def add_ship(self, ship):    # Блок размещение корабля
        for d in ship.dots:      # Проходится по точкам, отмечает их
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)  # Точки, где корабль, + соседствующие
        self.ships.append(ship)  # Добавляем в список собственных кораблей
        self.contour(ship)       # Обводим по контуру

    def contour(self, ship, verb=False):  # Точки соседствующие с кораблем
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:  # Ищем все точки соседствующие с кораблем
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:  # Не выходит за границы и не занята
                    if verb:     # Нужно ли ставить точки вокруг кораблей
                        self.field[cur.x][cur.y] = "X"
                    self.busy.append(cur)

    def __str__(self):
        res = ""
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | " + " | ".join(row) + " |"
        if self.hid:
            res = res.replace("■", "O")
        return res       # Записывается наша доска

    def out(self, d):    # Находится ли точка на доске. Если выходит -- отрицание условия
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def shot(self, d):
        if self.out(d):
            raise BoardOutException()
        if d in self.busy:
            raise BoardUsedException()
        self.busy.append(d)
        for ship in self.ships:     # Определяем принадлежит ли точка какому-то кораблю
            if d in ship.dots:      # Если выстрел с учетом поправки пришелся на точку:
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print("The ship is destroyed!")
                    return False
                else:
                    print("The ship is damaged!")
                    return True     # Повтор хода
        self.field[d.x][d.y] = "."
        print("Miss!")
        return False

    def begin(self):  # Готовим доску к игре, очищаем список занятых генерацией точек
        self.busy = []


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()


class Computer(Player):
    save_dx_dy = []        # Хранилище последнего случайного хода (+ первого попадания)
    save_dx_dy_two = []    # Хранилище проверенных точек (+ второе попадание)
    save_dx_dy_three = []  # Хранилище единственной пары координат для третьего выстрела (проверки на 3-х палубник)
    search_count = 0       # Счетчик точек которые необходимо проверить

    def move(self):        # Методы определены у каждого класса
        print(f"{self.__class__.__name__} running!")
        while True:
            try:
                d = self.ask()
                repeat = self.enemy.shot(d)
                self.flash_ship(repeat)
                # Компьютер регистрирует попадание, понимает что необходимо проверить соседние точки
                return repeat
            except BoardException as e:
                print(e)

    def flash_ship(self, repeat):
        if repeat:
            self.search_count += 4.0     # 4 -- Накрест лежащие точки, окружающие дот, в который попали

    def ask(self):
        if self.search_count > 4:        # Определяем ориентацию корабля, стреляем в одну 'Х'
            rx, ry = self.save_dx_dy_two[-1][0] - self.save_dx_dy[0], self.save_dx_dy_two[-1][1] - self.save_dx_dy[1]
            dot_x = self.save_dx_dy_two[-1][0] + rx  # Учтя ориентацию (rx, ry =0..1) получаем 2 точки для поиска
            dot_y = self.save_dx_dy_two[-1][1] + ry                                     # стреляем в одну
            self.save_dx_dy_three = [self.save_dx_dy[0] - rx, self.save_dx_dy[1] - ry]  # запоминаем другую
            self.save_dx_dy_two = []
            self.save_dx_dy = []         # Готовим список к переходу на ветку else
            self.search_count = 0
        elif self.save_dx_dy_three:   # Если корабль у края, или выбор не засчитывается -- стреляем в сохраненную точку
            dot_x = self.save_dx_dy_three[0]
            dot_y = self.save_dx_dy_three[1]
            self.save_dx_dy_three = []   # Выстрел один, после его совершения или вызова исключения хранилище будет []
        elif self.search_count > 0:      # Поиск второй точки
            while True:  # После первого попадания стреляем в накрест лежащие точки, пока не подобьем вторую точку
                dot_x = randint(self.save_dx_dy[0] - 1, self.save_dx_dy[0] + 1)
                dot_y = randint(self.save_dx_dy[1] - 1, self.save_dx_dy[1] + 1)
                if (self.save_dx_dy[0] != dot_x) or (self.save_dx_dy[1] != dot_y):  # получаем перекрестие
                    if (self.save_dx_dy[0] == dot_x) or (self.save_dx_dy[1] == dot_y):
                        dot_xy = [dot_x, dot_y]
                        if (dot_x not in range(0, 6) or dot_y not in range(0, 6)) or (dot_xy in self.save_dx_dy_two):
                            self.search_count -= 0.05  # Если корабль на границе и прицелиться на каждую точку Х нельзя
                            if self.search_count < 1:         # уходим от зацикливания, считая что корабль уничтожен
                                break
                            else:
                                continue
                        else:
                            self.save_dx_dy_two.append(dot_xy)
                            self.search_count -= 1  # Если точка будет проверена, переходим на ветку случайного выстрела
                            break
        else:    # Если ни один корабль не подбит, совершаем случайный выстрел
            dot_x, dot_y = randint(0, 5), randint(0, 5)
            self.save_dx_dy, self.save_dx_dy_two = [dot_x, dot_y], []
        d = Dot(dot_x, dot_y)
        print(f"The {self.__class__.__name__} shoots at: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    def ask(self):
        while True:
            cords = input("Your move: ").split()
            if len(cords) != 2:
                print(" Enter two coordinates! ")
                continue
            x, y = cords
            if not (x.isdigit()) or not (y.isdigit()):
                print(" Enter the numbers! ")
                continue
            x, y = int(x), int(y)
            return Dot(x - 1, y - 1)

    def move(self):
        print(f"{self.__class__.__name__} running!")
        while True:
            try:
                d = self.ask()
                repeat = self.enemy.shot(d)
                return repeat
            except BoardException as e:
                print(e)


class Game:
    num = 1  # Счетчик номера хода
    history_of_battles = []         # Список сохраняющий количество не уничтоженных кораблей игроков
    lens = [3, 2, 2, 1, 1, 1, 1]    # Рекомендуемые длины кораблей

    def __init__(self, size=6):
        self.size = size
        pl = self.random_board()    # Создаем два экземпляра класса Board
        co = self.random_board()
        co.hid = True
        self.ai = Computer(co, pl)  # Создаем два экземпляра класса Game
        self.user = User(pl, co)

    # Блок подсчета результатов игроков
    @classmethod
    def score_func(cls, result=None):
        if result is not None:
            cls.history_of_battles.append(result)  # формирования списка истории сражений
        num_game = int(len(cls.history_of_battles))
        score_pl = sum(1 if item[0] > item[1] else 0 for item in cls.history_of_battles)
        score_ai = sum(1 if item[1] > item[0] else 0 for item in cls.history_of_battles)
        _ = 's' if num_game == 1 else ''
        time.sleep(1)
        return f"For {num_game} game{_} the score:\n User vs Computer: {score_pl} : {score_ai} "

    def random_board(self):  # Запрос на генерацию случайных карт каждому экземпляру класса Game
        board = None
        while board is None:  # Цикл завершается если карта успешно сгенерирована
            board = self.random_place()
        return board

    def random_place(self):  # Блок генерации случайных карт (расположения кораблей)
        board = Board(size=self.size)
        attempts = 0
        for dimension in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:  # Сброс на начало в случае неудачного расположения
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), dimension, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()  # готовим доску к игре
        return board   # возвращаем доску

    # Блок проверки условия победы
    def victory_condition(self):
        lot = len(self.lens)
        if (self.ai.board.count == lot) or (self.user.board.count == lot):
            print("-" * 20)
            result = [lot - self.user.board.count, lot - self.ai.board.count]
            self.score_func(result)  # Запрос и возвращение информации о счете за все игры
            self.print_boards()      # Отображения доски после последнего выстрела
            time.sleep(1)
            if self.ai.board.count == lot:
                print(f"The {self.user.__class__.__name__} won!")
            if self.user.board.count == lot:
                print(f"The {self.ai.__class__.__name__} won!")
            return True

    # Блок отображения игрового поля
    def print_boards(self):
        print("-" * 62)
        print(f"{' ' * 9} {self.user.__class__.__name__} board:{' ' * 20} {self.ai.__class__.__name__} board:")
        left_board, right_board = str(self.user.board), str(self.ai.board)
        for left, right in zip(left_board.split('\n'), right_board.split('\n')):
            print(left, "  |  ", right)  # Отображение полей параллельно

    @classmethod
    def number_of_moves(cls, arg):
        if arg == '_next':
            cls.num += 1
        elif arg == '_back':
            cls.num -= 1
        else:
            cls.num = 1  # Сброс счетчика при начале новой игры
        return cls.num   # Вывод номера хода

    #  Блок игрового цикла
    def loop(self):
        queue = randint(0, 1)    # Очередность хода определяется случайно
        win = False
        while not win:
            self.print_boards()  # Запрос на отображение игровых полей
            print("-" * 62)
            if self.num % 2 == queue:
                repeat = self.user.move()
            else:
                repeat = self.ai.move()
            if repeat:
                self.number_of_moves('_back')  # Повтор хода при успешном попадании
            win = self.victory_condition()     # Проверка условий победы
            article = 'The ' if self.num <= 20 or self.num % 10 == 0 else ''
            print(f'{article}{self.num} move: ')  # Отображение номена хода
            self.number_of_moves('_next')      # Следующий ход

    @staticmethod
    def greet():
        print("-------------------")
        print("  Приветствуем вас ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    # Блок игровой последовательности
    def start(self):
        self.greet()      # приветствие
        while True:
            self.loop()   # Игровой цикл
            print(self.score_func())
            restart = self.new_game()  # Запрос на создание новой игры пользователю
            if restart == 3:
                print("Shutdown...")
                time.sleep(3)
                break
            else:
                continue

    # Блок выбора финального действия
    def new_game(self):
        while True:
            choice = input("1. New game!\n2. Show the history of battles \n3. End game\n")
            try:
                choice = int(choice)
            except ValueError:
                print(f"Incorrect input: {choice}. Please repeat")
                continue
            choice = int(choice)
            time.sleep(1)
            if choice > 3 or choice < 1:
                print(f"Incorrect input: {choice}. Please repeat")
                continue
            if choice == 1:  # Новая игра (путем повторного создания объектов класса)
                co = self.random_board()
                pl = self.random_board()
                self.user = User(pl, co)
                self.ai = Computer(co, pl)
                co.hid = True
                self.number_of_moves("_New")
                return '_Restart!'
            elif choice == 2:  # История битв, показывает сколько кораблей осталось у объектов в каждом сражении
                print(f'Number of remaining ships \n{self.user.__class__.__name__}/{self.ai.__class__.__name__}:')
                for _battle, _attempt in enumerate(self.history_of_battles):
                    print(f'{_battle + 1}g. :  {_attempt}')
                continue
            elif choice == 3:  # Выбор завершения игры
                return choice


g = Game()
g.start()
