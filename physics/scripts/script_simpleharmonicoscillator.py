import asyncio
import json
import pyodide
import numpy as np

from js import Bokeh, console, JSON
from bokeh import __version__
from bokeh.embed.util import OutputDocumentFor, standalone_docs_json_and_render_items
from bokeh.plotting import figure
from bokeh.models import Slider, Range1d, Spacer, Div
from bokeh.layouts import Column, Row
from bokeh.protocol.messages.patch_doc import process_document_events


#### CONTROLS, CALLBACKS, AND CALCULATIONS ############################                

# Initial values
slider_amplitude_initialvalue = 0.5
slider_frequency_initialvalue = 0.5

# Sliders
slider_amplitude = Slider(start=0, end=1, value=slider_amplitude_initialvalue, step=0.1, title="Amplitude (A)", height=50, sizing_mode="scale_width")
slider_frequency = Slider(start=0, end=1, value=slider_frequency_initialvalue, step=0.1, title="Frequency (f)", height=50, sizing_mode="scale_width")

# Variables
def x_fn():
    x = np.linspace(0, 10, 200)
    return x
def y_fn(amplitude,frequency,x):
    y = amplitude*np.sin(2*np.pi*frequency*x)
    return y

# Plot
plot1 = figure(height=200, sizing_mode="stretch_width")
plot1.x_range = Range1d(0,10)
plot1.y_range = Range1d(-1,1)
plot1.xaxis.axis_label = "x"
plot1.yaxis.axis_label = "y = A sin(2pi f x)"
plot1.xaxis.axis_label_text_font_style = "normal" 
plot1.yaxis.axis_label_text_font_style = "normal" 
plot1.line(x_fn(),y_fn(slider_amplitude_initialvalue,slider_frequency_initialvalue,x_fn()),line_width=2)

# Layout
sliders = Column(slider_amplitude, slider_frequency, sizing_mode="scale_width")
plots = Row(plot1, sizing_mode="scale_width")

# Callback
def update_data(attrname, old, new):
    amplitude = slider_amplitude.value
    frequency = slider_frequency.value
    
    x = x_fn()
    y = y_fn(amplitude,frequency,x)
    
    plot1.renderers.clear()
    plot1.line(x,y,line_width=2)

slider_amplitude.on_change('value', update_data)
slider_frequency.on_change('value', update_data)



#### RENDERING ############################
def doc_json(model, target):
    with OutputDocumentFor([model]) as doc:
        doc.title = ""
        docs_json, _ = standalone_docs_json_and_render_items(
            [model], suppress_callback_warning=True
        )
    doc_json = list(docs_json.values())[0]
    root_id = doc_json['roots']['root_ids'][0]

    return doc, json.dumps(dict(
        target_id = target,
        root_id   = root_id,
        doc       = doc_json,
        version   = __version__,
    ))

def _link_docs(pydoc, jsdoc):
    def jssync(event):
        if getattr(event, 'setter_id', None) is not None:
            return
        events = [event]
        json_patch = jsdoc.create_json_patch_string(pyodide.ffi.to_js(events))
        pydoc.apply_json_patch(json.loads(json_patch))

    jsdoc.on_change(pyodide.ffi.create_proxy(jssync), pyodide.ffi.to_js(False))

    def pysync(event):
        json_patch, buffers = process_document_events([event], use_buffers=True)
        buffer_map = {}
        for (ref, buffer) in buffers:
            buffer_map[ref['id']] = buffer
        jsdoc.apply_json_patch(JSON.parse(json_patch), pyodide.ffi.to_js(buffer_map), setter_id='js')

    pydoc.on_change(pysync)

async def show(object, target):
    pydoc, model_json = doc_json(object, target)
    views = await Bokeh.embed.embed_item(JSON.parse(model_json))
    jsdoc = views[0].model.document
    _link_docs(pydoc, jsdoc)

asyncio.ensure_future(show(sliders, 'sliders_learningpyscript'))
asyncio.ensure_future(show(plots, 'plots_learningpyscript'))


