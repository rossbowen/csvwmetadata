#%% Initial stuff to import the code.

import sys
from pathlib import Path

if __package__ is None:                  
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name
 
from csvwmetadata import *

#%% Table class gives you what you need to define a CSVW table.

Table(
    context = Context(),  # Add a CSVW context.
    url="hello",          # You must provide required properties.
    dcterms_title="Hello" # You may also add arbitrary JSON-LD.
)

# %% Incrementally build up a CSVW using helper methods.

t = Table(url="Hello")
t.add_context(base="http://example.org")
t.add_schema()
t.add_column(name="example", id="123", type="Column")
t.add_column(name="example")
# t.write("./example.json")

# %% Commands can be chained.

t = (
    Table(url="Hello")
    .add_context(base="http://example.org")
    .add_schema(id="#schema")
    .add_column(name="example", id="123", type="Column")
    .add_column(name="region")
)

# %%
# Attribute appears correctly parsed inside dict output.
# Also available as an attribute.

t.dcterms_title = "Hello World!"
t.dcterms_title
# %% You can set attributes whose names are URLs like this:

setattr(t, "http://example.co.uk", "example")
getattr(t, "http://example.co.uk")
# %% Setting common properties which aren't in the CSVW context will error.

t.madeup_example = "will error"

#%% Setting common properties which are relative URLs will error.

setattr(t, "#relative", "will error")

# %% Attributes can be set by using dict methods.

t["http://example2.co.uk"] = "example"
getattr(t, "http://example2.co.uk")

# %% Classes inherit successfully, allowing inhertied properties to be set

t.aboutUrl = "http://example.com"

# %%

# Common properites can be added using standard key value dict methods
# and are then available as attributes e.g. t.dcterms_example

t["dcterms:example4"] = "http://example"
print(t.dcterms_example4)

# %% JSON-LD @ properties are handled correctly

t.id = "http://example.org"
print(t["@id"])
