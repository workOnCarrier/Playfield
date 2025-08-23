# what is planuml
This is the toolkit used to generate diagrams from text description in <fileame>.puml files using the setup below for _*vscode*_.

## install PlantUML - Simple Viewer
https://marketplace.visualstudio.com/items?itemName=well-ar.plantuml

## run in docker locally
```
docker run -d -p 8089:8080 plantuml/plantuml-server:tomcat
```
## change PlantUML extension settings to target local PlantUML server
Planuml: Render
```
LocalServer
```
Plantuml: Server
```
http://localhost:8089
```

## working file creation
Create files as per the intened format in one of the many fomrats from the website -- https://plantuml.com/
Once you have the intended text format, run the below commands to see the diagram generated
### mac
```
opt + d
```
### others
```
Alt + d
```
