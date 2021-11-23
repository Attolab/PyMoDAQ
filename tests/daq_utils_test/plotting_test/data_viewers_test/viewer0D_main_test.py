from qtpy import QtWidgets, QtCore
import numpy as np
import pytest

from pymodaq.daq_utils import daq_utils as utils
from pymodaq.daq_utils.plotting.data_viewers.viewer0D import Viewer0D, default_label_formatter
from collections import OrderedDict

from pymodaq.daq_utils.conftests import qtbotskip
pytestmark = pytest.mark.skipif(qtbotskip, reason='qtbot issues but tested locally')

@pytest.fixture
def init_prog(qtbot):
    form = QtWidgets.QWidget()
    prog = Viewer0D(form)
    form.show()
    qtbot.addWidget(form)
    yield prog, qtbot
    form.close()


def init_data():
    x = np.linspace(0, 20, 21)
    y1 = utils.gauss1D(x, 12, 4)
    y2 = utils.gauss1D(x, 5, 8, 2)
    return x, y1, y2


class TestViewer0D:
    def test_init(self, init_prog):
        prog, qtbot = init_prog
        assert isinstance(prog, Viewer0D)
        assert isinstance(prog.parent, QtWidgets.QWidget)
        assert prog.title == 'viewer0D'
        
        prog = Viewer0D(None)
        assert isinstance(prog.parent, QtWidgets.QWidget)

    def test_show_data_as_list(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()

        for ind, data in enumerate(y1):
            prog.show_data([[data], [y2[ind]]])
            QtWidgets.QApplication.processEvents()

    def test_show_data_as_data_from_plugins(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()

        for y11, y22 in zip(y1, y2):
            datas = utils.DataFromPlugins(dim='Data0D', data=[np.array([y11]), np.array([y22])])
            prog.show_data(datas)
            QtWidgets.QApplication.processEvents()
            assert prog.labels == [default_label_formatter(ind) for ind in range(len(datas['data']))]

    def test_show_data_and_change_labels(self, init_prog):
        prog, qtbot = init_prog
        datas = utils.DataFromPlugins(dim='Data0D', data=[np.array([2.7]), np.array([9.6])])
        prog.show_data(datas)
        assert prog.labels == [default_label_formatter(ind) for ind in range(len(datas['data']))]

        NEW_LABELS = ['labelA', 'labelB']
        datas = utils.DataFromPlugins(dim='Data0D', data=[np.array([2.7]), np.array([9.6])],
                                      labels=NEW_LABELS)
        prog.show_data(datas)
        assert prog.labels == NEW_LABELS

        WRONG_LABELS = ['labelA', ]
        prog.show_data(datas)
        assert prog.labels != WRONG_LABELS

        datas = utils.DataFromPlugins(dim='Data0D', data=[np.array([2.7]), np.array([9.6]), np.array([34.6])])
        assert prog.labels == [default_label_formatter(ind) for ind in range(len(datas['data']))]

    def test_clear_pb(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()

        for ind, data in enumerate(y1):
            prog.show_data([[data], [y2[ind]]])
            QtWidgets.QApplication.processEvents()

        for data in prog.datas:
            assert data.size != 0
        assert prog.x_axis.size != 0

        qtbot.mouseClick(prog.ui.clear_pb, QtCore.Qt.LeftButton)

        for data in prog.datas:
            assert data.size == 0
        assert prog.x_axis.size == 0

    def test_Nhistory_sb(self, init_prog):
        prog, qtbot = init_prog

        assert prog.ui.Nhistory_sb.value() == 200
        prog.ui.Nhistory_sb.clear()
        qtbot.keyClicks(prog.ui.Nhistory_sb, '300')
        assert prog.ui.Nhistory_sb.value() == 300

    def test_show_datalist_pb(self, init_prog):
        prog, qtbot = init_prog

        prog.parent.show()

        qtbot.mouseClick(prog.ui.show_datalist_pb, QtCore.Qt.LeftButton)
        assert prog.ui.values_list.isVisible()
        qtbot.mouseClick(prog.ui.show_datalist_pb, QtCore.Qt.LeftButton)
        assert not prog.ui.values_list.isVisible()
        
    def test_clear_data(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        for ind, data in enumerate(y1):
            prog.show_data([[data], [y2[ind]]])
            QtWidgets.QApplication.processEvents()
        
        for data in prog.datas:
            assert len(data) > 0
        assert len(prog.x_axis) > 0

        prog.clear_data()

        for data in prog.datas:
            assert data.size == 0
        assert prog.x_axis.size == 0

    def test_show_data_list(self, init_prog):
        prog, qtbot = init_prog
        prog.parent.show()

        prog.ui.show_datalist_pb.setChecked(True)
        assert not prog.ui.values_list.isVisible() == prog.ui.show_datalist_pb.isChecked()
        prog.show_data_list(None)
        assert prog.ui.values_list.isVisible() == prog.ui.show_datalist_pb.isChecked()
        
    def test_show_data_temp(self, init_prog):
        prog, qtbot = init_prog
        
        assert not prog.show_data_temp(None)

    def test_update_Graph1D(self, init_prog):
        prog, qtbot = init_prog

        datas = np.linspace(np.linspace(1, 10, 10), np.linspace(11, 20, 10), 2)

        prog.datas = datas
        prog.Nsamples = 10
        prog.x_axis = np.linspace(1, 19, 19)

        prog.plot_channels = []
        for i in range(2):
            channel = prog.ui.Graph1D.plot(y=np.array([]))
            channel.setPen(1)
            prog.plot_channels.append(channel)

        prog.data_to_export = OrderedDict(data0D={})

        prog.update_Graph1D(datas)

        assert np.array_equal(prog.plot_channels[0].getData(), np.array((np.array(prog.x_axis),
                                                                         np.append(datas[0], datas[0])[1:])))
        assert np.array_equal(prog.plot_channels[1].getData(), np.array((np.array(prog.x_axis),
                                                                         np.append(datas[1], datas[1])[1:])))

        assert prog.data_to_export['data0D']['CH000']
        assert prog.data_to_export['data0D']['CH001']

        data_tot = np.array([np.append(datas[0], datas[0])[1:], np.append(datas[1], datas[1])[1:]])
        assert np.array_equal(np.array(prog.datas), data_tot)

    def test_update_channels(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        for ind, data in enumerate(y1):
            prog.show_data([[data], [y2[ind]]])
            QtWidgets.QApplication.processEvents()
            
        assert prog.plot_channels
        prog.update_channels()
        assert prog.plot_channels is None
        
    def test_update_labels(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        
        for ind, data in enumerate(y1):
            prog.show_data([[data], [y2[ind]]])
            QtWidgets.QApplication.processEvents()

        assert len(prog.plot_channels) == 2
        labels = ['axis_1', 'axis_2']
        prog.labels = labels
        for item, label in zip(prog.legend.items, labels):
            assert item[1].text == label
        
    def test_update_status(self, init_prog):
        prog, qtbot = init_prog
        
        assert not prog.update_status(txt='test')
        
    def test_update_x_axis(self, init_prog):
        prog, qtbot = init_prog
        
        Nhistory = 50
        prog.update_x_axis(Nhistory=Nhistory)
        
        assert prog.Nsamples == Nhistory
        assert np.array_equal(prog.x_axis, np.linspace(0, Nhistory - 1, Nhistory))

    def test_labels(self, init_prog):
        prog, qtbot = init_prog

        assert not prog.labels
        prog.labels = 'test_label'
        assert prog.labels == 'test_label'


