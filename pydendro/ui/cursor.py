# taken from from matploblib.widgets.

# XXX: need to put their copyright notice in...

from matplotlib.pylab import searchsorted

class Cursor:
    """
    A horizontal and vertical line span the axes that and move with
    the pointer.  You can turn off the hline or vline spectively with
    the attributes

      horizontal = True|False: controls visibility of the horizontal line
      vertical   = True|False: controls visibility of the horizontal line

    And the visibility of the cursor itself with visible attribute
    """
    def __init__(self, ax, 
                 useblit=False, tolerance=0.35,
                 vertical=True, horizontal=False, 
                 **lineprops):
        """
        Add a cursor to ax.  If useblit=True, use the backend
        dependent blitting features for faster updates (GTKAgg only
        now).  lineprops is a dictionary of line properties.  See
        examples/widgets/cursor.py.
        """
        self.ax = ax
        self.canvas = ax.figure.canvas

        self.canvas.mpl_connect('motion_notify_event', self.onmove)
        self.canvas.mpl_connect('draw_event', self.clear)

        self.visible = True
        self.horizontal = horizontal
        self.vertical = vertical
        self.useblit = useblit
        self.tolerance = tolerance

        self.lineh = ax.axhline(ax.get_ybound()[0], visible=False, **lineprops)
        self.linev = ax.axvline(ax.get_xbound()[0], visible=False, **lineprops)

        self.background = None
        self.needclear = False


    def clear(self, event):
        'clear the cursor'
        if self.useblit:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.linev.set_visible(False)
        self.lineh.set_visible(False)

    def onmove(self, event):
        'on mouse motion draw the cursor if visible'
        if event.inaxes != self.ax:
            self.linev.set_visible(False)
            self.lineh.set_visible(False)

            if self.needclear:
                self.canvas.draw()
                self.needclear = False
            return
        self.needclear = True
        if not self.visible: return

        x, y = event.xdata, event.ydata

        try:
            if self.x[0] <= x and x <= self.x[-1]:
                indx = searchsorted(self.x, [x-0.48])[0]

                x = self.x[indx]
                
                # if abs(x - self.x[indx]) < self.tolerance:
                #     x = self.x[indx]
                #     self.vertical = True
                # else:
                #     self.vertical = False
        except:
            x = event.xdata
        
        self.linev.set_xdata((x, x))
        self.lineh.set_ydata((y, y))
        self.linev.set_visible(self.visible and self.vertical)
        self.lineh.set_visible(self.visible and self.horizontal)

        self._update()


    def _update(self):

        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.linev)
            self.ax.draw_artist(self.lineh)
            self.canvas.blit(self.ax.bbox)
        else:

            self.canvas.draw_idle()

        return False
