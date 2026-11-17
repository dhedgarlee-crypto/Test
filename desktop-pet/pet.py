"""
데스크톱 펫 - 화면 위를 돌아다니는 작은 친구

실행:  python pet.py   (또는 run.bat 더블클릭)
조작:
  - 왼쪽 클릭     : 반가워해요 (점프 + 하트)
  - 드래그        : 집어서 옮기기 (놓으면 떨어져요)
  - 오른쪽 클릭   : 메뉴 (앉아 / 자 / 점프 / 마우스 따라오기 / 크기 / 하나 더 / 종료)
  - 트레이 아이콘 : 종료
"""
import math
import random
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QCursor, QIcon,
                           QPainter, QPainterPath, QPen, QPixmap, QTransform)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

# ───────────────────────── 설정 ─────────────────────────
FPS = 30
BASE_SIZE = 96          # 캐릭터 기본 크기(px)
WALK_SPEED = 2.0        # 걷기 속도(px/프레임)
RUN_SPEED = 5.5         # 뛰기 속도
GRAVITY = 0.9
JUMP_POWER = 13.0
SPRITE_DIR = Path(__file__).resolve().parent / "sprites"
ANIM_FPS = {"idle": 3, "walk": 8, "run": 14, "jump": 6, "sit": 2,
            "sleep": 1.5, "drag": 6, "happy": 8}

# 상태별 지속시간(초)과 다음 상태로 갈 확률
NEXT_STATE = {
    "idle":  [("walk", 45), ("run", 15), ("jump", 10), ("sit", 20), ("idle", 10)],
    "walk":  [("idle", 40), ("walk", 25), ("run", 15), ("jump", 10), ("sit", 10)],
    "run":   [("walk", 40), ("idle", 30), ("jump", 30)],
    "sit":   [("idle", 50), ("sleep", 35), ("walk", 15)],
    "sleep": [("sit", 60), ("idle", 40)],
}
DURATION = {"idle": (1.5, 4), "walk": (2, 6), "run": (1, 2.5),
            "sit": (3, 8), "sleep": (8, 20), "happy": (1.2, 1.2)}


# ───────────────────── 기본 캐릭터(콩이) ─────────────────────
# sprites/ 폴더에 그림이 없을 때 쓰는 오리지널 캐릭터.
# 동글동글한 주황색 콩에 새싹이 하나 달린 친구예요.
BODY = QColor("#F6A65A")
BODY_DARK = QColor("#D9803A")
LEAF = QColor("#7CC46B")
LINE = QColor("#5A3A22")
CHEEK = QColor(255, 120, 120, 140)


def draw_kongi(state: str, frame: int, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 100.0
    p.scale(s, s)

    t = frame
    bob = 0.0
    squash = 1.0
    leg_phase = 0.0
    eyes = "open"
    if state == "idle":
        bob = [0, 1.5][t % 2]
        eyes = "blink" if t % 6 == 5 else "open"
    elif state in ("walk", "run"):
        bob = abs(math.sin(t * math.pi / 2)) * (3 if state == "walk" else 6)
        leg_phase = math.sin(t * math.pi / 2)
    elif state == "jump":
        squash = 0.92
    elif state == "sit":
        squash = 1.08
        eyes = "blink" if t % 5 == 4 else "open"
    elif state == "sleep":
        squash = 1.1
        bob = [0, 1][t % 2]
        eyes = "closed"
    elif state == "drag":
        eyes = "wide"
        leg_phase = math.sin(t * math.pi / 2)
    elif state == "happy":
        eyes = "happy"
        bob = [0, 3][t % 2]

    cx, ground = 50, 92
    w, h = 62 * squash, 58 / squash
    top = ground - h - 6 - bob + (6 if state in ("sit", "sleep") else 0)

    # 발
    p.setPen(Qt.NoPen)
    p.setBrush(BODY_DARK)
    if state not in ("sit", "sleep"):
        for side in (-1, 1):
            off = leg_phase * 6 * side
            p.drawEllipse(QRectF(cx + side * 14 - 7 + off, ground - 9, 14, 9))

    # 몸통
    body = QRectF(cx - w / 2, top, w, h)
    p.setPen(QPen(LINE, 2.2))
    p.setBrush(BODY)
    p.drawEllipse(body)

    # 팔
    p.setBrush(BODY)
    arm_y = top + h * 0.58
    if state in ("drag", "happy", "jump"):
        for side in (-1, 1):
            p.drawEllipse(QRectF(cx + side * (w / 2 - 2) - 6, arm_y - 16, 12, 12))
    else:
        swing = leg_phase * 3
        for side in (-1, 1):
            p.drawEllipse(QRectF(cx + side * (w / 2 - 3) - 5, arm_y + swing * side, 10, 10))

    # 새싹
    stem_top = QPointF(cx + 2, top - 12)
    p.setPen(QPen(LEAF.darker(130), 2.5))
    p.drawLine(QPointF(cx, top + 1), stem_top)
    p.setPen(QPen(LEAF.darker(140), 1.5))
    p.setBrush(LEAF)
    wiggle = math.sin(t * 0.8) * 4 if state in ("walk", "run", "happy") else 0
    for side in (-1, 1):
        leaf = QPainterPath()
        leaf.moveTo(stem_top)
        tip = QPointF(stem_top.x() + side * 14, stem_top.y() - 6 + wiggle * side)
        leaf.quadTo(QPointF(stem_top.x() + side * 7, stem_top.y() - 14), tip)
        leaf.quadTo(QPointF(stem_top.x() + side * 8, stem_top.y() + 2), stem_top)
        p.drawPath(leaf)

    # 얼굴 (오른쪽을 보는 방향, 살짝 오른쪽으로 치우침)
    fx, fy = cx + 6, top + h * 0.45
    p.setPen(QPen(LINE, 2.4))
    p.setBrush(LINE)
    for ex in (fx - 10, fx + 10):
        if eyes == "open":
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(ex - 3, fy - 4, 6, 8))
            p.setBrush(Qt.white)
            p.drawEllipse(QRectF(ex - 1, fy - 3, 2.4, 2.4))
            p.setBrush(LINE)
        elif eyes == "wide":
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(ex - 4, fy - 5, 8, 10))
            p.setBrush(Qt.white)
            p.drawEllipse(QRectF(ex - 1.5, fy - 4, 3, 3))
            p.setBrush(LINE)
        elif eyes == "happy":
            p.setPen(QPen(LINE, 2.4))
            p.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(ex - 4, fy + 1)
            path.quadTo(ex, fy - 6, ex + 4, fy + 1)
            p.drawPath(path)
            p.setBrush(LINE)
        else:  # blink / closed
            p.setPen(QPen(LINE, 2.4))
            p.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(ex - 4, fy)
            path.quadTo(ex, fy + 4, ex + 4, fy)
            p.drawPath(path)
            p.setBrush(LINE)

    # 볼
    p.setPen(Qt.NoPen)
    p.setBrush(CHEEK)
    for ex in (fx - 17, fx + 17):
        p.drawEllipse(QRectF(ex - 5, fy + 5, 10, 6))

    # 입
    p.setPen(QPen(LINE, 2))
    p.setBrush(Qt.NoBrush)
    mouth = QPainterPath()
    if eyes in ("wide",):
        p.setBrush(QColor("#C0504D"))
        p.drawEllipse(QRectF(fx - 3, fy + 7, 6, 6))
    elif eyes == "happy":
        p.setBrush(QColor("#C0504D"))
        mouth.moveTo(fx - 5, fy + 7)
        mouth.quadTo(fx, fy + 15, fx + 5, fy + 7)
        mouth.closeSubpath()
        p.drawPath(mouth)
    else:
        mouth.moveTo(fx - 4, fy + 8)
        mouth.quadTo(fx - 2, fy + 11, fx, fy + 8)
        mouth.quadTo(fx + 2, fy + 11, fx + 4, fy + 8)
        p.drawPath(mouth)

    # Zzz
    if state == "sleep":
        p.setPen(QPen(QColor("#6A7FDB"), 2))
        f = p.font()
        f.setBold(True)
        for i, ch in enumerate("zZ"):
            f.setPointSizeF(8 + i * 3)
            p.setFont(f)
            p.drawText(QPointF(cx + 24 + i * 9, top - 2 - i * 9 - (t % 2) * 3), ch)

    p.end()
    return pm


def load_frames(size: int) -> dict:
    """sprites/ 폴더의 PNG를 읽고, 없으면 기본 캐릭터를 그려요."""
    states = list(ANIM_FPS.keys())
    frames = {}
    for st in states:
        files = sorted(SPRITE_DIR.glob(f"{st}_*.png"),
                       key=lambda f: int(f.stem.split("_")[-1]) if f.stem.split("_")[-1].isdigit() else 0)
        imgs = [QPixmap(str(f)) for f in files]
        imgs = [i.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                for i in imgs if not i.isNull()]
        if imgs:
            frames[st] = imgs
    if "idle" not in frames:  # 사용자 그림이 없으면 기본 캐릭터
        return {st: [draw_kongi(st, i, size) for i in range(4 if st != "idle" else 6)]
                for st in states}
    for st in states:
        frames.setdefault(st, frames["idle"])
    return frames


# ───────────────────────── 펫 창 ─────────────────────────
class Pet(QWidget):
    instances = []

    def __init__(self, size=BASE_SIZE, start_x=None):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        Pet.instances.append(self)

        self.size_px = size
        self.frames = load_frames(size)
        self.flipped = {}
        self.setFixedSize(size, size + 24)   # 위쪽 24px는 하트용 여유 공간

        self.state = "idle"
        self.frame = 0
        self.anim_acc = 0.0
        self.state_left = 2.0
        self.facing = random.choice([-1, 1])
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.follow_mouse = False
        self.dragging = False
        self.drag_offset = QPoint()
        self.press_pos = None
        self.drag_history = []
        self.hearts = []   # [x, y, life]

        area = self.area()
        x = start_x if start_x is not None else random.randint(area.left(), area.right() - size)
        self.fx, self.fy = float(x), float(area.top())   # 위에서 떨어지며 등장
        self.move(int(self.fx), int(self.fy))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000 // FPS)
        self.show()

    # 펫이 있는 모니터의 작업 영역(작업표시줄 제외)
    def area(self):
        center = self.geometry().center() if self.isVisible() else QCursor.pos()
        screen = QApplication.screenAt(center) or QApplication.primaryScreen()
        return screen.availableGeometry()

    def ground_y(self):
        return self.area().bottom() - self.height() + 1

    # ───── 상태 ─────
    def set_state(self, st, duration=None):
        self.state = st
        self.frame = 0
        self.anim_acc = 0.0
        lo, hi = DURATION.get(st, (1, 2))
        self.state_left = duration if duration is not None else random.uniform(lo, hi)
        if st in ("walk", "run") and random.random() < 0.4:
            self.facing *= -1
        if st == "jump" and self.on_ground:
            self.vy = -JUMP_POWER * random.uniform(0.8, 1.1)
            self.vx = self.facing * random.uniform(2, 4)
            self.on_ground = False

    def pick_next(self):
        options = NEXT_STATE.get(self.state, NEXT_STATE["idle"])
        r = random.uniform(0, sum(w for _, w in options))
        for st, w in options:
            r -= w
            if r <= 0:
                return st
        return "idle"

    # ───── 매 프레임 ─────
    def tick(self):
        dt = 1 / FPS
        area = self.area()
        gy = self.ground_y()

        if not self.dragging:
            # 마우스 따라오기
            if self.follow_mouse and self.on_ground and self.state not in ("happy",):
                mx = QCursor.pos().x() - self.width() / 2
                dist = mx - self.fx
                if abs(dist) > 30:
                    self.facing = 1 if dist > 0 else -1
                    want = "run" if abs(dist) > 250 else "walk"
                    if self.state != want:
                        self.set_state(want, 999)
                elif self.state in ("walk", "run"):
                    self.set_state("idle", 999)

            # 이동
            if self.state == "walk":
                self.vx = WALK_SPEED * self.facing
            elif self.state == "run":
                self.vx = RUN_SPEED * self.facing
            elif self.on_ground:
                self.vx = 0

            # 중력
            if not self.on_ground:
                self.vy += GRAVITY
                self.vx *= 0.99
            self.fx += self.vx
            self.fy += self.vy

            if self.fy >= gy:
                self.fy = gy
                if not self.on_ground:
                    self.on_ground = True
                    self.vy = 0
                    if self.state in ("jump", "drag"):
                        self.set_state("idle")
            elif self.fy < gy - 1:
                self.on_ground = False

            # 화면 가장자리에서 돌아서기
            left, right = area.left(), area.right() - self.width() + 1
            if self.fx <= left:
                self.fx, self.facing = left, 1
                self.vx = abs(self.vx)
            elif self.fx >= right:
                self.fx, self.facing = right, -1
                self.vx = -abs(self.vx)

            # 상태 타이머
            if self.on_ground and self.state not in ("jump", "drag"):
                self.state_left -= dt
                if self.state_left <= 0 and not self.follow_mouse:
                    self.set_state(self.pick_next())
                elif self.state_left <= 0:
                    self.set_state("idle", 999)

            self.move(int(self.fx), int(self.fy))

        # 애니메이션
        self.anim_acc += dt * ANIM_FPS.get(self.state, 4)
        if self.anim_acc >= 1:
            self.anim_acc -= 1
            self.frame += 1

        # 하트
        for h in self.hearts:
            h[1] -= 1.2
            h[2] -= dt
        self.hearts = [h for h in self.hearts if h[2] > 0]
        self.update()

    # ───── 그리기 ─────
    def current_pixmap(self):
        imgs = self.frames.get(self.state) or self.frames["idle"]
        pm = imgs[self.frame % len(imgs)]
        if self.facing < 0:
            key = (self.state, self.frame % len(imgs))
            if key not in self.flipped:
                self.flipped[key] = pm.transformed(QTransform().scale(-1, 1))
            pm = self.flipped[key]
        return pm

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pm = self.current_pixmap()
        p.drawPixmap((self.width() - pm.width()) // 2, self.height() - pm.height(), pm)
        for x, y, life in self.hearts:
            p.setOpacity(max(0.0, min(1.0, life)))
            self.draw_heart(p, x, y, 9)
        p.end()

    @staticmethod
    def draw_heart(p, x, y, r):
        path = QPainterPath()
        path.moveTo(x, y + r * 0.9)
        path.cubicTo(x - r * 1.6, y - r * 0.2, x - r * 0.6, y - r * 1.4, x, y - r * 0.4)
        path.cubicTo(x + r * 0.6, y - r * 1.4, x + r * 1.6, y - r * 0.2, x, y + r * 0.9)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#FF6B8B")))
        p.drawPath(path)

    # ───── 마우스 ─────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.press_pos = e.globalPosition().toPoint()
            self.drag_offset = self.press_pos - self.pos()
            self.drag_history = []

    def mouseMoveEvent(self, e):
        if self.press_pos is None:
            return
        gp = e.globalPosition().toPoint()
        if not self.dragging and (gp - self.press_pos).manhattanLength() > 6:
            self.dragging = True
            self.on_ground = False
            self.set_state("drag", 999)
        if self.dragging:
            pos = gp - self.drag_offset
            self.fx, self.fy = float(pos.x()), float(pos.y())
            self.move(pos)
            self.drag_history = (self.drag_history + [pos])[-4:]

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.dragging:
            self.dragging = False
            # 던지기: 마지막 움직임 속도를 이어받아요
            if len(self.drag_history) >= 2:
                d = self.drag_history[-1] - self.drag_history[0]
                n = len(self.drag_history) - 1
                self.vx = max(-25, min(25, d.x() / n))
                self.vy = max(-25, min(25, d.y() / n))
            else:
                self.vx = self.vy = 0
            self.set_state("jump", 999)
            self.on_ground = False
        elif self.on_ground:
            self.be_happy()
        self.press_pos = None

    def be_happy(self):
        self.set_state("happy")
        self.vy = -7
        self.on_ground = False
        self.hearts.append([self.width() / 2 + random.uniform(-15, 15), 24.0, 1.4])

    def contextMenuEvent(self, e):
        m = QMenu(self)
        m.addAction("앉아", lambda: self.set_state("sit"))
        m.addAction("자", lambda: self.set_state("sleep"))
        m.addAction("점프", lambda: self.set_state("jump", 999))
        m.addAction("산책", lambda: self.set_state("walk"))
        m.addSeparator()
        fm = QAction("마우스 따라오기", m, checkable=True, checked=self.follow_mouse)
        fm.toggled.connect(self.toggle_follow)
        m.addAction(fm)
        sm = m.addMenu("크기")
        grp = QActionGroup(sm)
        for label, mul in (("작게", 0.7), ("보통", 1.0), ("크게", 1.4), ("아주 크게", 2.0)):
            a = QAction(label, sm, checkable=True, checked=int(BASE_SIZE * mul) == self.size_px)
            a.triggered.connect(lambda _=False, s=int(BASE_SIZE * mul): self.resize_pet(s))
            grp.addAction(a)
            sm.addAction(a)
        m.addSeparator()
        m.addAction("친구 하나 더", lambda: Pet(self.size_px, int(self.fx)))
        m.addAction("이 친구 보내기", self.close)
        m.addAction("모두 종료", QApplication.quit)
        m.exec(e.globalPos())

    def toggle_follow(self, on):
        self.follow_mouse = on
        self.set_state("idle")

    def resize_pet(self, size):
        self.size_px = size
        self.frames = load_frames(size)
        self.flipped = {}
        bottom = self.fy + self.height()
        self.setFixedSize(size, size + 24)
        self.fy = bottom - self.height()
        self.update()

    def closeEvent(self, e):
        if self in Pet.instances:
            Pet.instances.remove(self)
        if not Pet.instances:
            QApplication.quit()
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = Pet()

    tray = QSystemTrayIcon(QIcon(draw_kongi("idle", 0, 64)), app)
    menu = QMenu()
    menu.addAction("친구 하나 더", lambda: Pet())
    menu.addAction("종료", app.quit)
    tray.setContextMenu(menu)
    tray.setToolTip("데스크톱 펫")
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
