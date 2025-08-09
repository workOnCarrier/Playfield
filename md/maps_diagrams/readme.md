# planuml

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
