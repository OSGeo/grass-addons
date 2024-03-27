import io
import sys
import urllib.request
import urllib.parse
import urllib.error

from . import globalvar

# Header levels
H1, H2, H3, H4, H5, H6, T1, T2, T3, T4 = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

# List styles
UL, OL = 0, 1

# Titles

# Alignment
CENTER, LEFT, RIGHT = "CENTER", "LEFT", "RIGHT"


class MySheet:
    _stylesheet1_undefined = object()

    def __init__(self):
        try:
            global ParagraphStyle, TA_CENTER, _baseFontName, _baseFontNameB, _baseFontNameBI, _baseFontNameI, colors, inch

            from reportlab.lib.styles import (
                ParagraphStyle,
                _baseFontNameB,
                _baseFontNameI,
                _baseFontNameBI,
            )
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.rl_config import canvas_basefontname as _baseFontName
            from reportlab.lib.enums import TA_CENTER
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.byName = {}
        self.byAlias = {}

    def __getitem__(self, key):
        try:
            return self.byAlias[key]
        except KeyError:
            try:
                return self.byName[key]
            except KeyError:
                raise KeyError("Style '%s' not found in stylesheet" % key)

    def get(self, key, default=_stylesheet1_undefined):
        try:
            return self[key]
        except KeyError:
            if default != _stylesheet1_undefined:
                return default
            raise

    def __contains__(self, key):
        return key in self.byAlias or key in self.byName

    def has_key(self, key):
        return key in self

    def add(self, style, alias=None):
        key = style.name
        if key in self.byName:
            raise KeyError("Style '%s' already defined in stylesheet" % key)
        if key in self.byAlias:
            raise KeyError("Style name '%s' is already an alias in stylesheet" % key)

        if alias:
            if alias in self.byName:
                raise KeyError("Style '%s' already defined in stylesheet" % alias)
            if alias in self.byAlias:
                raise KeyError(
                    "Alias name '%s' is already an alias in stylesheet" % alias
                )
        # passed all tests?  OK, add it
        self.byName[key] = style
        if alias:
            self.byAlias[alias] = style

    def list(self):
        styles = sorted(self.byName.items())
        alii = {}
        for alias, style in list(self.byAlias.items()):
            alii[style] = alias
        for name, style in styles:
            alias = alii.get(style, None)
            style.listAttrs("    ")

    def getSampleStyleSheet(self):
        """Returns a stylesheet object"""
        stylesheet = MySheet()

        stylesheet.add(
            ParagraphStyle(
                name="Normal", fontName=_baseFontName, fontSize=10, leading=12
            )
        )
        stylesheet.add(
            ParagraphStyle(
                name="Title",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameB,
                fontSize=18,
                leading=22,
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
            alias="title",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Title2",
                parent=stylesheet["Normal"],
                fontName=_baseFontName,
                fontSize=13,
                leading=22,
                alignment=TA_CENTER,
                spaceAfter=0,
            ),
            alias="title2",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Title3",
                parent=stylesheet["Normal"],
                fontName=_baseFontName,
                fontSize=10,
                leading=5,
                alignment=TA_CENTER,
                spaceAfter=10,
            ),
            alias="title3",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Title4",
                parent=stylesheet["Normal"],
                fontName=_baseFontName,
                fontSize=8,
                leading=10,
                alignment=TA_CENTER,
                spaceAfter=5,
            ),
            alias="title4",
        )

        stylesheet.add(
            ParagraphStyle(name="BodyText", parent=stylesheet["Normal"], spaceBefore=6)
        )
        stylesheet.add(
            ParagraphStyle(
                name="Italic", parent=stylesheet["BodyText"], fontName=_baseFontNameI
            )
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading1",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameB,
                fontSize=18,
                leading=22,
                spaceAfter=6,
            ),
            alias="h1",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading2",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameB,
                fontSize=14,
                leading=18,
                spaceBefore=12,
                spaceAfter=6,
            ),
            alias="h2",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading3",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameBI,
                fontSize=12,
                leading=14,
                spaceBefore=12,
                spaceAfter=6,
            ),
            alias="h3",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading4",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameBI,
                fontSize=10,
                leading=12,
                spaceBefore=10,
                spaceAfter=4,
            ),
            alias="h4",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading5",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameB,
                fontSize=9,
                leading=10.8,
                spaceBefore=8,
                spaceAfter=4,
            ),
            alias="h5",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Heading6",
                parent=stylesheet["Normal"],
                fontName=_baseFontNameB,
                fontSize=7,
                leading=8.4,
                spaceBefore=6,
                spaceAfter=2,
            ),
            alias="h6",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Bullet",
                parent=stylesheet["Normal"],
                firstLineIndent=0,
                spaceBefore=3,
            ),
            alias="bu",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Definition",
                parent=stylesheet["Normal"],
                firstLineIndent=0,
                leftIndent=36,
                bulletIndent=0,
                spaceBefore=6,
                bulletFontName=_baseFontNameBI,
            ),
            alias="df",
        )

        stylesheet.add(
            ParagraphStyle(
                name="Code",
                parent=stylesheet["Normal"],
                fontName="Courier",
                fontSize=8,
                leading=8.8,
                firstLineIndent=0,
                leftIndent=36,
            )
        )

        return stylesheet


class DefaultTheme(object):
    def __init__(self):
        self.s = MySheet()
        self._s = self.s.getSampleStyleSheet()

        self.doc = {
            "leftMargin": None,
            "rightMargin": None,
            "topMargin": None,
            "bottomMargin": None,
        }
        self.headers = {
            H1: self._s["Heading1"],
            H2: self._s["Heading2"],
            H3: self._s["Heading3"],
            H4: self._s["Heading4"],
            H5: self._s["Heading5"],
            H6: self._s["Heading6"],
            T1: self._s["Title"],
            T2: self._s["Title2"],
            T3: self._s["Title3"],
            T4: self._s["Title4"],
        }

        self.paragraph = self._s["Normal"]

        self.spacer_height = 0.25 * inch
        self.table_style = [
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C0C0C0")),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#E0E0E0")],
            ),
        ]

    def doc_template_args(
        self,
    ):
        return dict([(k, v) for k, v in list(self.doc.items()) if v is not None])

    def header_for_level(self, level):
        return self.headers[level]


def calc_table_col_widths(rows, table_width):
    max_chars_per_col = [0] * len(rows[0])
    for row in rows:
        for idx, col in enumerate(row):
            for line in str(col).split("\n"):
                max_chars_per_col[idx] = max(len(line), max_chars_per_col[idx])
    sum_chars = sum(max_chars_per_col)
    return [(x * table_width / sum_chars) for x in max_chars_per_col]


_stylesheet1_undefined = object()


class Pdf(object):
    story = []
    theme = DefaultTheme

    def __init__(self, title, author):
        try:
            global Image, KeepTogether, LongTable, Paragraph, SimpleDocTemplate, Spacer, Table

            from reportlab.platypus.doctemplate import SimpleDocTemplate
            from reportlab.platypus.flowables import Image
            from reportlab.platypus import Paragraph, Spacer, KeepTogether
            from reportlab.platypus.tables import Table, LongTable
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.title = title
        self.author = author

    def set_theme(self, theme):
        self.theme = theme

    def add(self, flowable):
        self.story.append(flowable)

    def add_header(self, text, level=H1):
        p = Paragraph(text, self.theme.header_for_level(level))
        self.add(p)

    def add_fparagraph(self, text, style=None):
        if style is not None:
            self.add(Table([[text]], style=style))
        else:
            self.add(Table([[text]]))

    def add_spacer(self, height_inch=None):
        height_inch = height_inch or self.theme.spacer_height
        self.add(
            Spacer(1, height_inch)
        )  # magic 1? no, first param not yet implemented by rLab guys

    def add_paragraph(self, text, style=None):
        style = style or self.theme.paragraph
        p = Paragraph(text, style)
        self.add(p)

    def add_list(self, items, list_style=UL):
        raise NotImplementedError

    def add_table(
        self, rows, width=None, col_widths=None, align=CENTER, extra_style=[]
    ):
        style = self.theme.table_style + extra_style
        if (
            width and col_widths is None
        ):  # one cannot spec table width in rLab only col widths
            col_widths = calc_table_col_widths(
                rows, width
            )  # this helper calcs it for us
        table = LongTable(rows, col_widths, style=style, hAlign=align)
        self.add(table)

    def add_image(self, src, width, height, align=CENTER):
        img = Image(src, width, height)
        img.hAlign = align
        self.add(img)

    def render(self):
        buffer = io.BytesIO()
        doc_template_args = self.theme.doc_template_args()
        doc = SimpleDocTemplate(
            buffer, title=self.title, author=self.author, **doc_template_args
        )
        doc.build(self.story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
