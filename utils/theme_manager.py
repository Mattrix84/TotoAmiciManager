from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QPalette, QColor, QFont, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QCoreApplication, QPointF, QRect, QPoint

class ThemeManager:
    
    @staticmethod
    def set_football_theme(app):
        app.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()

        # Colori ispirati al calcio, con priorità al cielo
        grass_green = QColor(120, 190, 100)  # Verde erba più chiaro
        sky_blue = QColor(135, 206, 235)  # Azzurro cielo
        white = QColor(255, 255, 255)  # Bianco
        dark_blue = QColor(25, 25, 112)  # Blu notte per il contrasto
        light_grey = QColor(240, 240, 240)  # Grigio chiaro
        beige = QColor(245, 245, 220)  # Beige per un tocco di calore

        # Sfondo con gradiente: cielo dominante e erba in basso
        gradient = QLinearGradient(0, 300, 300, 1000)
        gradient.setColorAt(0, sky_blue.lighter(110))  # Cielo in alto
        gradient.setColorAt(0.55, sky_blue.lighter(120))  # Cielo che si schiarisce leggermente
        gradient.setColorAt(0.6, grass_green.lighter(130))  # Inizio della transizione
        gradient.setColorAt(1, grass_green.lighter(130))  # Verde in basso

        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, QBrush(gradient))
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QBrush(gradient))

        # Resto dei colori
        palette.setColor(QPalette.ColorRole.WindowText, dark_blue)
        palette.setColor(QPalette.ColorRole.Base, white)
        palette.setColor(QPalette.ColorRole.AlternateBase, light_grey)
        palette.setColor(QPalette.ColorRole.ToolTipBase, beige)
        palette.setColor(QPalette.ColorRole.ToolTipText, dark_blue)
        palette.setColor(QPalette.ColorRole.Text, dark_blue)
        palette.setColor(QPalette.ColorRole.Button, sky_blue.lighter(150))  # Bottoni più chiari
        palette.setColor(QPalette.ColorRole.ButtonText, sky_blue)
        palette.setColor(QPalette.ColorRole.BrightText, white)
        palette.setColor(QPalette.ColorRole.Link, sky_blue.darker(140))
        palette.setColor(QPalette.ColorRole.Highlight, dark_blue)
        palette.setColor(QPalette.ColorRole.HighlightedText, white)

        app.setPalette(palette)

        # Impostiamo un font moderno e leggibile
        font = QFont("Segoe UI", 10)
        app.setFont(font)

    @staticmethod
    def set_custom_football_style(widget):
        # Stile personalizzato per widget specifici
        widget.setStyleSheet("""
            QPushButton {
                background-color: rgba(135, 206, 235, 180);  /* Sky blue with some transparency */
                color: #191970;  /* Midnight blue */
                border: 1px solid #4682B4;  /* Steel blue */
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(176, 224, 230, 200);  /* Powder blue with some transparency */
            }
            QPushButton:disabled {
                background-color: rgba(224, 224, 224, 180);
                color: #A9A9A9;
                border: 1px solid #D3D3D3;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: rgba(255, 255, 255, 180);  /* Slightly transparent white */
                border: 1px solid #87CEEB;
                padding: 3px;
                border-radius: 3px;
            }
            QTableWidget {
                gridline-color: #B0E0E6;
                background-color: rgba(255, 255, 255, 180);
                alternate-background-color: rgba(240, 248, 255, 180);  /* Alice blue with transparency */
            }
            QHeaderView::section {
                background-color: rgba(70, 130, 180, 200);  /* Steel blue with some transparency */
                color: white;
                padding: 5px;
                border: 1px solid #4169E1;  /* Royal blue */
            }
        """)