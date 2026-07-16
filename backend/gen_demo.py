import ifcopenshell

f = ifcopenshell.file(schema="IFC4")

# Project structure
project = f.create_entity("IfcProject", GlobalId="0", Name="Demo Project")
site = f.create_entity("IfcSite", GlobalId="1", Name="Site")
building = f.create_entity("IfcBuilding", GlobalId="2", Name="Building")
storey = f.create_entity("IfcBuildingStorey", GlobalId="3", Name="Ground Floor")

f.create_entity("IfcRelAggregates", GlobalId="r1", RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId="r2", RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId="r3", RelatingObject=building, RelatedObjects=[storey])

# Walls (missing FireRating)
walls = []
for i in range(4):
    w = f.create_entity("IfcWall", GlobalId=f"w{i}", Name=f"Wall-{i+1}")
    walls.append(w)

# Doors with various widths
doors = []
widths = [800, 750, 1000, 900, 600]
for i, w in enumerate(widths):
    d = f.create_entity("IfcDoor", GlobalId=f"d{i}", Name=f"Door-{i+1}",
                        OverallWidth=w, OverallHeight=2100)
    doors.append(d)

f.create_entity("IfcRelContainedInSpatialStructure", GlobalId="rc1",
                RelatedElements=walls + doors, RelatingStructure=storey)

f.write("D:/Python/Projects/hku-bim-checker/samples/demo.ifc")
print("Created demo.ifc with", len(walls), "walls and", len(doors), "doors")
