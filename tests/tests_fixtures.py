"""Hand-written XES FORMAT fixtures for parser/loader tests. Not data."""

FIXTURE_WITH_OUTLIER = """<?xml version="1.0" encoding="UTF-8"?>
<log xes.version="1.0" xmlns="http://www.xes-standard.org/">
  <trace>
    <string key="concept:name" value="DOC1_00010"/>
    <string key="Purchasing Document" value="DOC1"/>
    <string key="Item" value="00010"/>
    <string key="Item Category" value="3-way match, invoice after GR"/>
    <string key="Vendor" value="vendorA"/>
    <string key="Name" value="vendor A name"/>
    <string key="Company" value="companyID_0000"/>
    <string key="Document Type" value="Standard PO"/>
    <boolean key="Goods Receipt" value="true"/>
    <boolean key="GR-Based Inv. Verif." value="true"/>
    <event>
      <string key="concept:name" value="Create Purchase Order Item"/>
      <date key="time:timestamp" value="2018-01-02T10:00:00.000+01:00"/>
      <string key="User" value="user_001"/>
      <string key="org:resource" value="user_001"/>
      <float key="Cumulative net worth (EUR)" value="100.0"/>
    </event>
    <event>
      <string key="concept:name" value="Record Goods Receipt"/>
      <date key="time:timestamp" value="2018-01-05T10:00:00.000+01:00"/>
      <float key="Cumulative net worth (EUR)" value="100.0"/>
    </event>
    <event>
      <string key="concept:name" value="Record Invoice Receipt"/>
      <date key="time:timestamp" value="1948-01-27T00:00:00.000+01:00"/>
      <float key="Cumulative net worth (EUR)" value="100.0"/>
    </event>
  </trace>
  <trace>
    <string key="concept:name" value="DOC1_00020"/>
    <string key="Purchasing Document" value="DOC1"/>
    <string key="Item" value="00020"/>
    <string key="Item Category" value="2-way match"/>
    <string key="Vendor" value="vendorA"/>
    <string key="Name" value="vendor A name"/>
    <event>
      <string key="concept:name" value="Create Purchase Order Item"/>
      <date key="time:timestamp" value="2018-02-01T09:00:00.000+01:00"/>
    </event>
  </trace>
</log>
"""
