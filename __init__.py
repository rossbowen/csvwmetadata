from __future__ import annotations

import json
from collections import UserDict, UserList
from typing import Any, List, Optional, Union
from urllib.parse import urlparse

from uritemplate import URITemplate

_PREFIXES = {
    "as": "https://www.w3.org/ns/activitystreams#",
    "cc": "http://creativecommons.org/ns#",
    "csvw": "http://www.w3.org/ns/csvw#",
    "ctag": "http://commontag.org/ns#",
    "dc": "http://purl.org/dc/terms/",
    "dc11": "http://purl.org/dc/elements/1.1/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcterms": "http://purl.org/dc/terms/",
    "dctypes": "http://purl.org/dc/dcmitype/",
    "dqv": "http://www.w3.org/ns/dqv#",
    "duv": "https://www.w3.org/TR/vocab-duv#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "gr": "http://purl.org/goodrelations/v1#",
    "grddl": "http://www.w3.org/2003/g/data-view#",
    "ical": "http://www.w3.org/2002/12/cal/icaltzd#",
    "ldp": "http://www.w3.org/ns/ldp#",
    "ma": "http://www.w3.org/ns/ma-ont#",
    "oa": "http://www.w3.org/ns/oa#",
    "og": "http://ogp.me/ns#",
    "org": "http://www.w3.org/ns/org#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "prov": "http://www.w3.org/ns/prov#",
    "qb": "http://purl.org/linked-data/cube#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfa": "http://www.w3.org/ns/rdfa#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rev": "http://purl.org/stuff/rev#",
    "rif": "http://www.w3.org/2007/rif#",
    "rr": "http://www.w3.org/ns/r2rml#",
    "schema": "http://schema.org/",
    "sd": "http://www.w3.org/ns/sparql-service-description#",
    "sioc": "http://rdfs.org/sioc/ns#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "skosxl": "http://www.w3.org/2008/05/skos-xl#",
    "v": "http://rdf.data-vocabulary.org/#",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "void": "http://rdfs.org/ns/void#",
    "wdr": "http://www.w3.org/2007/05/powder#",
    "wrds": "http://www.w3.org/2007/05/powder-s#",
    "xhv": "http://www.w3.org/1999/xhtml/vocab#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}

def is_absolute_uri(uri):
    """
    Returns bool whether a given URI is absolute.
    """
    return bool(urlparse(uri).netloc)


def prefixer(key: str) -> str:
    """
    Converts prefixes provided via kwargs in the format prefix_name into the
    recognised JSON-LD format of prefix:name.
    """
    return key.replace("_", ":")


def unprefixer(key: str) -> str:
    """
    Converts prefixes provided via kwargs in the recognised JSON-LD format of
    prefix:name into syntatic sugar of the form prefix_name.
    """
    return key.replace(":", "_")


def is_valid_prefix(key: dict):
    """
    https://w3c.github.io/csvw/metadata/#names-of-common-properties

    The prefixes that are recognized are those defined for [rdfa-core] within
    the RDFa 1.1 Initial Context and other prefixes defined within
    [csvw-context] and these MUST NOT be overridden. These prefixes are
    periodically extended; refer to [csvw-context] for details. Properties
    from other vocabularies MUST be named using absolute URLs.

    https://www.w3.org/ns/csvw.jsonld
    """
    return bool(key.split(":")[0] in _PREFIXES.keys())


class CommonProperties(UserDict):
    """https://w3c.github.io/csvw/metadata/#common-properties"""
    _valid_properties = []

    def __setattr__(self, name: str, value: Any) -> None:
        """
        We overwrite the __setattr__ method to enforce only valid common
        properties may be added.
        """
        if name == "data":
            return super().__setattr__(name, value)
        # Handling for JSON-LD @ properties.
        elif name in ["id", "type", "context"]:
            attr = "@" + name
            self.data[attr] = value
            return super().__setattr__(name , value)
        elif name not in self._valid_properties:
            attr = prefixer(name)
            if is_valid_prefix(attr) or is_absolute_uri(attr):
                self.data[attr] = value
                return super().__setattr__(name, value)
            else:
                raise ValueError(
                    "Common properies must either be absolute URLs, or of " +
                    "the form prefix:name, where prefix must be defined " +
                    "within the CSVW context, see: " +
                    "https://w3c.github.io/csvw/metadata/#names-of-common-properties"
                )
        else:
            self.data[name] = value
            return super().__setattr__(name, value)

    def __setitem__(self, key, item) -> None:
        """
        We overwrite the __setitem___ method so that key value pairs added using
        dict methods are also accesible via attributes.
        """

        # When setting a prefix common property using a dict method, e.g.
        # csvw["dcterms:title"] = "My Example Title",
        # we want the attribute to be available with some syntactic sugar e.g.
        # csvw.dcterms_title.
        attr = key
        if key not in self._valid_properties:
            attr = unprefixer(key) if not is_absolute_uri(key) else key
        setattr(self, attr, item)
        return super().__setitem__(key, item)


class TopLevelProperty(CommonProperties):
    """
    The top-level object of a metadata document or object referenced through an
    object property (whether it is a table group description, table description,
    schema, dialect description or transformation definition) MUST have a
    `@context` property. This is an array property, as defined in Section 8.7 of
    [JSON-LD]. The `@context` MUST have one of the following values:
    """

    @property
    def context(self) -> Union[str, dict]:
        return self.data["@context"]

    @context.setter
    def context(self, value: Union[str, dict]):
        if isinstance(value, dict):
            value = Context(**value)
        if not isinstance(value, Context):
            raise ValueError("Value must be of type Context or dict.")
        self.data["@context"] = value

    def add_context(
        self, base: Optional[str] = None, language: Optional[str] = None
    ):
        self.context = Context(base, language)
        return self

    def write(self, filename: str, **kwargs):
        with open(filename, "w") as file_:
            file_.write(json.dumps(self.data, default=lambda x: vars(x)[
                        "data"], indent=4, **kwargs))


class Context(UserList):
    def __init__(self, base: Optional[str] = None, language: Optional[str] = None):
        if not (base or language):
            context = "http://www.w3.org/ns/csvw"
        else:
            context = ["http://www.w3.org/ns/csvw", {}]
            if base:
                context[1]["@base"] = base
            if language:
                context[1]["@language"] = language
        self.data = context

    @property
    def base(self):
        pass

    @property
    def language(self):
        pass


class InheritedProperties(UserDict):
    _inherited_properties: List = [
        "aboutUrl", "datatype", "default", "lang", "null", "ordered", 
        "propertyUrl", "required", "separator", "textDirection", "valueUrl"
    ]
    
    @property
    def aboutUrl(self) -> URITemplate:
        """
        A URI template property that MAY be used to indicate what a cell
        contains information about. The value of this property becomes the about
        URL annotation for the described column and is used to create the value
        of the about URL annotation for the cells within that column as
        described in § 5.1.3 URI Template Properties.

        `aboutUrl` is typically defined on a schema description or table
        description to indicate what each row is about. If defined on individual
        column descriptions, care must be taken to ensure that transformed cell
        values maintain a semantic relationship.
        """
        return self.data["aboutUrl"]

    @aboutUrl.setter
    def aboutUrl(self, value: URITemplate):
        self.data["aboutUrl"] = value

    @property
    def datatype(self) -> str:
        """
        An atomic property that contains either a single string that is the main
        datatype of the values of the cell or a datatype description object. If
        the value of this property is a string, it MUST be the name of one of
        the built-in datatypes defined in § 5.11.1 Built-in Datatypes and this
        value is normalized to an object whose base property is the original
        string value. If it is an object then it describes a more specialized
        datatype. If a cell contains a sequence (i.e. the separator property is
        specified and not null) then this property specifies the datatype of
        each value within that sequence. See § 5.11 Datatypes and Parsing Cells
        in [tabular-data-model] for more details.

        The normalized value of this property becomes the datatype annotation
        for the described column.
        """
        return self.data["datatype"]

    @datatype.setter
    def datatype(self, value: str):
        self.data["datatype"] = value

    @property
    def default(self) -> str:
        """
        An atomic property holding a single string that is used to create a
        default value for the cell in cases where the original string value is
        an empty string. See Parsing Cells in [tabular-data-model] for more
        details. If not specified, the default for the default property is the
        empty string, `""`. The value of this property becomes the default
        annotation for the described column.
        """
        return self.data["default"]

    @default.setter
    def default(self, value: str):
        self.data["default"] = value

    @property
    def lang(self) -> str:
        """
        An atomic property giving a single string language code as defined by
        [BCP47]. Indicates the language of the value within the cell. See
        Parsing Cells in [tabular-data-model] for more details. The value of
        this property becomes the lang annotation for the described column. The
        default is `und`.
        """
        return self.data["lang"]

    @lang.setter
    def lang(self, value: str):
        self.data["lang"] = value

    @property
    def null(self) -> str:
        """
        An atomic property giving the string or strings used for null values
        within the data. If the string value of the cell is equal to any one of
        these values, the cell value is `null`. See Parsing Cells in
        [tabular-data-model] for more details. If not specified, the default for
        the `null` property is the empty string `""`. The value of this property
        becomes the null annotation for the described column.
        """
        return self.data["null"]

    @null.setter
    def null(self, value: str):
        self.data["null"] = value

    @property
    def ordered(self) -> bool:
        """
        A boolean atomic property taking a single value which indicates whether
        a list that is the value of the cell is ordered (if `true`) or unordered
        (if `false`). The default is false. This property is irrelevant if the
        `separator` is `null` or undefined, but this is not an error. The value
        of this property becomes the ordered annotation for the described
        column, and the ordered annotation for the cells within that column.
        """
        return self.data["ordered"]

    @ordered.setter
    def ordered(self, value: bool):
        self.data["ordered"] = value

    @property
    def propertyUrl(self) -> URITemplate:
        """
        A URI template property that MAY be used to create a URI for a property
        if the table is mapped to another format. The value of this property
        becomes the property URL annotation for the described column and is used
        to create the value of the property URL annotation for the cells within
        that column as described in § 5.1.3 URI Template Properties.

        `propertyUrl` is typically defined on a column description. If defined
        on a schema description, table description or table group description,
        care must be taken to ensure that transformed cell values maintain an
        appropriate semantic relationship, for example by including the name of
        the column in the generated URL by using `_name` in the template.
        """
        return self.data["propertyUrl"]

    @propertyUrl.setter
    def propertyUrl(self, value: URITemplate):
        self.data["propertyUrl"] = value

    @property
    def required(self) -> bool:
        """
        A boolean atomic property taking a single value which indicates whether
        the cell value can be null. See Parsing Cells in [tabular-data-model]
        for more details. The default is false, which means cells can have null
        values. The value of this property becomes the required annotation for
        the described column.
        """
        return self.data["required"]

    @required.setter
    def required(self, value: bool):
        self.data["required"] = value

    @property
    def separator(self) -> str:
        """
        An atomic property that MUST have a single string value that is the
        string used to separate items in the string value of the cell. If `null`
        (the default) or unspecified, the cell does not contain a list.
        Otherwise, application MUST split the string value of the cell on the
        specified separator and parse each of the resulting strings separately.
        The cell's value will then be a list. See Parsing Cells in
        [tabular-data-model] for more details. The value of this property
        becomes the separator annotation for the described column.
        """
        return self.data["separator"]

    @separator.setter
    def separator(self, value: str):
        self.data["separator"] = value

    @property
    def textDirection(self) -> str:
        """
        An atomic property that MUST have a single string value that is one of
        `"ltr"`, `"rtl"`, `"auto"` or `"inherit"` (the default). Indicates
        whether the text within cells should be displayed as left-to-right text
        (`ltr`), as right-to-left text (`rtl`), according to the content of the
        cell (`auto`) or in the direction inherited from the table direction
        annotation of the table. The value of this property determines the text
        direction annotation for the column, and the text direction annotation
        for the cells within that column: if the value is inherit then the value
        of the text direction annotation is the value of the table direction
        annotation on the table, otherwise it is the value of this property. See
        Bidirectional Tables in [tabular-data-model] for details.
        """
        return self.data["textDirection"]

    @textDirection.setter
    def textDirection(self, value: str):
        self.data["textDirection"] = value

    @property
    def valueUrl(self) -> URITemplate:
        """
        A URI template property that is used to map the values of cells into
        URLs. The value of this property becomes the value URL annotation for
        the described column and is used to create the value of the value URL
        annotation for the cells within that column as described in § 5.1.3 URI
        Template Properties.

        This allows processors to build URLs from cell values, for example to
        reference RDF resources, as defined in [rdf-concepts]. For example, if
        the value URL were `"{#reference}"`, each cell value of a column named
        reference would be used to create a URI such as
        `http://example.com/#1234`, if `1234` were a cell value of that column.

        `valueUrl` is typically defined on a column description. If defined on a
        schema description, table description or table group description, care
        must be taken to ensure that transformed cell values maintain an
        appropriate semantic relationship.
        """
        return self.data["valueUrl"]

    @valueUrl.setter
    def valueUrl(self, value: URITemplate):
        self.data["valueUrl"] = value


class Table(TopLevelProperty, CommonProperties, InheritedProperties):
    _common_properties: List = [
        "url", "notes", "dialect", "suppressOutput", "tableDirection",
        "tableSchema", "transformations", "id", "type"
    ]
    _valid_properties = [
        *InheritedProperties._inherited_properties,
        *_common_properties
    ]

    def __init__(
        self,
        url: str,
        dialect: Optional[str] = None,
        suppressOutput: Optional[bool] = None,
        tableDirection: Optional[str] = None,
        tableSchema: Optional[Schema] = None,
        transformations: Optional[str] = None,
        id: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs
    ) -> None:

        self.data = {}
        for attr, value in locals().items():
            if attr not in ("self", "kwargs") and value is not None:
                setattr(self, attr, value)
        for attr, value in kwargs.items():
            if value is not None:
                setattr(self, attr, value)

    @property
    def url(self) -> str:
        """
        This link property gives the single URL of the CSV file that the table
        is held in, relative to the location of the metadata document. The value
        of this property is the value of the url annotation for the annotated
        table this table description describes.
        """
        return self.data["url"]

    @url.setter
    def url(self, value: str):
        self.data["url"] = value

    @property
    def dialect(self):
        return self.data["dialect"]

    @dialect.setter
    def dialect(self, value: str):
        self.data["dialect"] = value

    @property
    def notes(self):
        return self.data["notes"]

    @notes.setter
    def notes(self, value: List[str]):
        """
        An array property that provides an array of objects representing
        arbitrary annotations on the annotated group of tables. The value of
        this property becomes the value of the notes annotation for the group of
        tables. The properties on these objects are interpreted equivalently to
        common properties as described in § 5.8 Common Properties.
        """
        if not isinstance(value, list):
            raise ValueError(
                "notes property of Table object must be a list of strings."
            )
        self.data["notes"] = value

    @property
    def suppressOutput(self):
        return self.data["suppressOutput"]

    @suppressOutput.setter
    def suppressOutput(self, value: bool):
        self.data["suppressOutput"] = value

    @property
    def tableDirection(self) -> str:
        return self.data["tableDirection"]

    @tableDirection.setter
    def tableDirection(self, value: str):
        if value not in ["rtl", "ltr", "auto"]:
            raise ValueError(
                "tableDirection must be one of 'rtl', 'ltr', or 'auto'."
            )
        self.data["tableDirection"] = value

    @property
    def tableSchema(self) -> Schema:
        return self.data["tableSchema"]

    @tableSchema.setter
    def tableSchema(self, value: Union[Schema, dict]):
        if isinstance(value, dict):
            value = Schema(**value)
        if not isinstance(value, Schema):
            raise ValueError("Value must be of type Schema or dict.")
        self.data["tableSchema"] = value

    @property
    def id(self):
        return self.data["@id"]

    @id.setter
    def id(self, value: str):
        self.data["@id"] = value

    @property
    def type(self):
        return self.data["@type"]

    @type.setter
    def type(self, value: str):
        if not value == "Table":
            raise ValueError("Type property of Table object must be 'Table'.")
        self.data["@type"] = value

    def add_schema(self, **kwargs):
        if not self.get("tableSchema"):
            self.tableSchema = Schema(**kwargs)
        else:
            raise AttributeError(
                "Table object already has a Schema attribute.")
        return self

    def add_column(self, **kwargs):
        if not self.get("tableSchema"):
            self.add_schema()
        self.tableSchema.add_column(**kwargs)
        return self


class Schema(TopLevelProperty, CommonProperties, InheritedProperties):
    _common_properties: List = [
        "name", "columns", "foreignKeys", "primaryKey", "rowTitles", "id", "type"
    ]
    _valid_properties = [
        *InheritedProperties._inherited_properties,
        *_common_properties
    ]

    def __init__(
        self,
        name: Optional[str] = None,
        columns: Optional[List[Column]] = None,
        foreignKeys: Optional[List[ForeignKey]] = None,
        primaryKey: Union[str, List[str]] = None,
        rowTitles: Optional[str] = None,
        id: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs
    ) -> None:

        self.data = {}
        for attr, value in locals().items():
            if attr not in ("self", "kwargs") and value is not None:
                setattr(self, attr, value)
        for attr, value in kwargs.items():
            if value is not None:
                setattr(self, attr, value)

    @property
    def columns(self) -> List[Column]:
        """
        An array property of column descriptions as described in § 5.6 Columns.
        These are matched to columns in tables that use the schema b y position:
        the first column description in the array applies to the first column in
        the table, the second to the second and so on.

        The `name` properties of the column descriptions MUST be unique within a
        given table description.
        """
        return self.data["columns"]

    @columns.setter
    def columns(self, value: str):
        if not isinstance(value, list):
            raise ValueError(
                "columns property of Schema object must be a list of Column " +
                "or dict objects."
            )
        names = [
            x.get("name") for x in self.columns if x.get("name") is not None
        ]
        if names is None:
            names = []
        if len(names) > len(set(names)):
            raise ValueError(
                "The name properties of the column descriptions MUST be " +
                "unique within a given table description."
            )
        self.data["columns"] = value

    @property
    def foreignKeys(self) -> list:
        """
        An array property of foreign key definitions that define how the values
        from specified columns within this table link to rows within this table
        or other tables.
        """
        return self.data["columns"]

    @foreignKeys.setter
    def foreignKeys(self, value: list):
        self.data["foreignKeys"] = value

    @property
    def primaryKey(self) -> Union[str, List[str]]:
        """
        A column reference property that holds either a single reference to a
        column description object or an array of references. The value of this
        property becomes the primary key annotation for each row within a table
        that uses this schema by creating a list of the cells in that row that
        are in the referenced columns.

        As defined in [tabular-data-model], validators MUST check that each row
        has a unique combination of values of cells in the indicated columns.
        For example, if `primaryKey` is set to `["familyName", "givenName"]`
        then every row must have a unique value for the combination of values of
        cells in the `familyName` and `givenName` columns.
        """
        return self.data["primaryKey"]

    @primaryKey.setter
    def primaryKey(self, value: Union[str, List[str]]):
        self.data["primaryKey"] = value

    @property
    def rowTitles(self) -> str:
        """
        A column reference property that holds either a single reference to a
        column description object or an array of references. The value of this
        property determines the titles annotation for each row within a table
        that uses this schema. The titles annotation holds the list of the
        values of the cells in that row that are in the referenced columns; if
        the value is not a string or has no associated language, it is
        interpreted as a string with an undefined language (`und`).
        """
        return self.data["rowTitles"]

    @rowTitles.setter
    def rowTitles(self, value: str):
        self.data["rowTitles"] = value

    def add_column(self, **kwargs):
        if not self.get("columns"):
            self.columns = []
        names = [
            x.get("name") for x in self.columns if x.get("name") is not None
        ]
        if names is None:
            names = []
        names.append(kwargs.get("name"))
        if len(names) > len(set(names)):
            raise ValueError(
                "The name properties of the column descriptions MUST be " +
                "unique within a given table description."
            )
        self.columns.append(Column(**kwargs))
        return self


class Column(CommonProperties, InheritedProperties):
    """
    A column description is a JSON object that describes a single column. The
    description provides additional human-readable documentation for a column,
    as well as additional information that may be used to validate the cells
    within the column, create a user interface for data entry, or inform
    conversion into other formats. All properties are optional.
    """

    _common_properties: List = [
        "name", "suppressOutput", "titles", "virtual", "id", "type"
    ]
    _valid_properties = [
        *InheritedProperties._inherited_properties,
        *_common_properties
    ]

    def __init__(
        self,
        name: Optional[str] = None,
        suppressOutput: Optional[bool] = None,
        titles: Optional[str] = None,
        virtual: Optional[bool] = None,
        id: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs
    ) -> None:

        self.data = {}
        for attr, value in locals().items():
            if attr not in ("self", "kwargs") and value is not None:
                setattr(self, attr, value)
        for attr, value in kwargs.items():
            if value is not None:
                setattr(self, attr, value)

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: bool):
        if value[0] == "_":
            raise ValueError(
                "'name' attribute must not begin with an underscore '_'"
            )
        self.data["name"] = value

    @property
    def suppressOutput(self) -> bool:
        return self.data["suppressOutput"]

    @suppressOutput.setter
    def suppressOutput(self, value: bool):
        self.data["suppressOutput"] = value

    @property
    def titles(self) -> bool:
        """
        A natural language property that provides possible alternative names for
        the column. The string values of this property, along with their
        associated language tags, become the titles annotation for the described
        column.

        If there is no `name` property defined on this column, the first
        `titles` value having the same language tag as default language, or
        `und` or if no default language is specified, becomes the name
        annotation for thedescribed column. This annotation MUST be
        percent-encoded as necessaryto conform to the syntactic requirements
        defined in [RFC3986].
        """
        return self.data["titles"]

    @titles.setter
    def titles(self, value: bool):
        self.data["titles"] = value

    @property
    def virtual(self) -> bool:
        """
        A boolean atomic property taking a single value which indicates whether
        the column is a virtual column not present in the original source. The
        default value is `false`. The normalized value of this property becomes
        the virtual annotation for the described column. If present, a virtual
        column MUST appear after all other non-virtual column definitions.
        """
        return self.data["virtual"]

    @virtual.setter
    def virtual(self, value: bool):
        self.data["virtual"] = value

class ForeignKey():
    pass
