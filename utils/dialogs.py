"""
utils/dialogs.py - Dialog utilities
"""

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView


class FunctionHelpDialog(QDialog):
    """Dialog displaying function descriptions with MathJax-rendered LaTeX formulas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Function Descriptions (LaTeX with MathJax)")
        self.setMinimumSize(800, 700)

        layout = QVBoxLayout(self)

        # WebEngineView to render HTML with MathJax
        self.web_view = QWebEngineView()

        # Raw string to avoid SyntaxWarning from backslashes in LaTeX
        html = r"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif;
                    background-color: #ffffff;
                    margin: 20px;
                    line-height: 1.6;
                }
                h2 {
                    color: #1a3b5d;
                    border-bottom: 2px solid #3b6ea5;
                    padding-bottom: 8px;
                }
                .func {
                    background-color: #f8fafd;
                    border-left: 6px solid #2c7be0;
                    border-radius: 0 8px 8px 0;
                    padding: 18px 22px;
                    margin: 25px 0;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                }
                .func h3 {
                    color: #1e4660;
                    margin-top: 0;
                    margin-bottom: 15px;
                    font-weight: 600;
                }
                .formula {
                    background-color: #e9eff7;
                    padding: 12px 18px;
                    border-radius: 8px;
                    font-size: 1.2em;
                    text-align: center;
                    margin: 15px 0;
                    overflow-x: auto;
                }
                .param-list {
                    display: grid;
                    grid-template-columns: auto 1fr;
                    gap: 8px 20px;
                    margin: 15px 0 0 0;
                }
                .param-name {
                    font-weight: 600;
                    color: #b22222;
                    font-family: 'Courier New', monospace;
                }
                .param-desc {
                    color: #2c3e50;
                }
                .note {
                    font-style: italic;
                    color: #4a6b8a;
                    margin-top: 15px;
                    padding-top: 10px;
                    border-top: 1px dashed #b0c4de;
                }
                .mjx-chtml {
                    font-size: 110% !important;
                }
            </style>
        </head>
        <body>
            <h2>📐 Refractive Index Functions</h2>
            <p>All functions assume axial symmetry. The radial coordinate is 
            \( r = \sqrt{(x - x_0)^2 + y^2} \), where \( x_0 \) is the horizontal shift (mm).</p>

            <!-- Gaussian -->
            <div class="func">
                <h3>🔹 Gaussian</h3>
                <div class="formula">
                    \[ n(r) = A + (B - A) \exp\left(-C \, r^{D}\right) \]
                </div>
                <div class="param-list">
                    <span class="param-name">\(A\)</span><span class="param-desc">background index (\(r \to \infty\))</span>
                    <span class="param-name">\(B\)</span><span class="param-desc">center index (\(r = 0\))</span>
                    <span class="param-name">\(C\)</span><span class="param-desc">decay rate (width)</span>
                    <span class="param-name">\(D\)</span><span class="param-desc">power (shape factor)</span>
                    <span class="param-name">\(x_0\)</span><span class="param-desc">horizontal shift (mm)</span>
                </div>
            </div>

            <!-- Lorentzian -->
            <div class="func">
                <h3>🔹 Lorentzian</h3>
                <div class="formula">
                    \[ n(r) = A + \frac{B - A}{1 + C \, r^{D}} \]
                </div>
                <div class="param-list">
                    <span class="param-name">\(A\)</span><span class="param-desc">background index</span>
                    <span class="param-name">\(B\)</span><span class="param-desc">center index</span>
                    <span class="param-name">\(C\)</span><span class="param-desc">width parameter</span>
                    <span class="param-name">\(D\)</span><span class="param-desc">power</span>
                    <span class="param-name">\(x_0\)</span><span class="param-desc">horizontal shift (mm)</span>
                </div>
            </div>

            <!-- Smoothed Step -->
            <div class="func">
                <h3>🔹 Smoothed Step</h3>
                <div class="formula">
                    \[ n(r) = A + \frac{B - A}{1 + \exp\bigl(D\,(r - C)\bigr)} \]
                </div>
                <div class="param-list">
                    <span class="param-name">\(A\)</span><span class="param-desc">index outside step (\(r \gg C\))</span>
                    <span class="param-name">\(B\)</span><span class="param-desc">index inside step (\(r \ll C\))</span>
                    <span class="param-name">\(C\)</span><span class="param-desc">step radius (mm)</span>
                    <span class="param-name">\(D\)</span><span class="param-desc">steepness (larger = sharper)</span>
                    <span class="param-name">\(x_0\)</span><span class="param-desc">horizontal shift (mm)</span>
                </div>
                <div class="note">For large \(D\) (e.g., \(>100\)) approximates an ideal step function.</div>
            </div>

            <!-- Parabolic -->
            <div class="func">
                <h3>🔹 Parabolic</h3>
                <div class="formula">
                    \[ n(r) = \begin{cases}
                        A + (B - A)\left(1 - (r/C)^2\right) & \text{if } r < C \\
                        A & \text{if } r \ge C
                    \end{cases} \]
                </div>
                <div class="param-list">
                    <span class="param-name">\(A\)</span><span class="param-desc">index at edge (\(r = C\)) and beyond</span>
                    <span class="param-name">\(B\)</span><span class="param-desc">index at center (\(r = 0\))</span>
                    <span class="param-name">\(C\)</span><span class="param-desc">radius (mm)</span>
                    <span class="param-name">\(x_0\)</span><span class="param-desc">horizontal shift (mm)</span>
                </div>
                <div class="note">Parameter \(D\) is ignored.</div>
            </div>
            
            <!-- Linear X -->
            <div class="func">
                <h3>🔹 Linear X</h3>
                <div class="formula">
                    \[ n(x) = A + B\,(x - x_0) \]
                </div>
                <div class="param-list">
                    <span class="param-name">\(A\)</span><span class="param-desc">refractive index at \(x = x_0\)</span>
                    <span class="param-name">\(B\)</span><span class="param-desc">gradient coefficient (dn/dx) [mm⁻¹]</span>
                    <span class="param-name">\(x_0\)</span><span class="param-desc">horizontal shift (mm)</span>
                </div>
                <div class="note">Parameters \(C\) and \(D\) are ignored.</div>
            </div>

            <div class="note">All parameters except \(x_0\) and \(C\) (where indicated) are dimensionless.</div>
        </body>
        </html>
        """

        self.web_view.setHtml(html)
        layout.addWidget(self.web_view)

        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)


def show_error_dialog(parent, title: str, message: str):
    QMessageBox.critical(parent, title, message)


def show_warning_dialog(parent, title: str, message: str):
    QMessageBox.warning(parent, title, message)


def show_info_dialog(parent, title: str, message: str):
    QMessageBox.information(parent, title, message)


def create_progress_dialog(parent, title: str = "Processing",
                          label: str = "Please wait..."):
    from PyQt5.QtWidgets import QProgressDialog
    dialog = QProgressDialog(label, "Cancel", 0, 100, parent)
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setAutoClose(True)
    dialog.setAutoReset(True)
    return dialog