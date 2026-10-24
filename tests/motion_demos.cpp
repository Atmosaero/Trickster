#include "core.h"
#include "motion_analysis.h"
#include "motion_annotations.h"
#include "retarget.h"
#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <iostream>
#include <set>
using namespace trickster;
QJsonObject note(QString name, double a, double b, QJsonArray nodes, QString type = "event") {
    return {{"name", name},       {"start", a},   {"end", b},
            {"nodes", nodes},     {"type", type}, {"provenance", "intention"},
            {"description", name}};
}
int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    QString directory = argc > 1 ? QString::fromLocal8Bit(argv[1]) : "examples/motion-tools";
    QDir().mkpath(directory);
    QString error;
    QJsonArray files;
    auto save = [&](QString name, Scene scene) {
        QString path = QDir(directory).filePath(name + ".trickster");
        if (!saveProject(path, scene, error))
            throw std::runtime_error(error.toStdString());
        files.append(QJsonObject{{"name", name}, {"project", QFileInfo(path).fileName()}});
        Scene reopened;
        if (!loadProject(path, reopened, error))
            throw std::runtime_error(error.toStdString());
        if (reopened.annotations != scene.annotations ||
            curvesJson(reopened.curves) != curvesJson(scene.curves))
            throw std::runtime_error("Project round trip lost authored context or curves");
        if (name == "annotated-jump" || name == "curves-paths" || name == "retarget-result") {
            QString output = "artifacts/motion-independent-input/" + name;
            QDir().mkpath(output);
            if (!exportGltf(output + "/result.glb", reopened, error) ||
                !exportFbx(output + "/result.fbx", reopened, error))
                throw std::runtime_error(error.toStdString());
            std::set<double> times;
            for (int i = 0; i <= 32; ++i)
                times.insert(double(scene.first) / scene.fps +
                             double(scene.last - scene.first) / scene.fps * i / 32);
            if (name == "curves-paths")
                for (double t : {.499, .5, .501, 1.249, 1.251, 2.124, 2.876, 3.749})
                    times.insert(t);
            QJsonArray expected;
            for (double t : times) {
                reopened.evaluate(float(t * reopened.fps));
                QJsonObject joints;
                QJsonArray vertices;
                auto positions = reopened.positions(reopened.pose);
                for (int n = 0; n < int(reopened.nodes.size()); ++n)
                    joints[reopened.nodes[n].name] =
                        QJsonArray{positions[n].x(), positions[n].y(), positions[n].z()};
                for (auto &mesh : reopened.meshes)
                    for (auto v : reopened.skinned(mesh))
                        vertices.append(QJsonArray{v.x(), v.y(), v.z()});
                expected.append(QJsonObject{{"seconds", t}, {"joints", joints}, {"vertices", vertices}});
            }
            QFile reference(output + "/expected.json");
            if (!reference.open(QIODevice::WriteOnly))
                throw std::runtime_error("Cannot write reference");
            reference.write(QJsonDocument(expected).toJson(QJsonDocument::Compact));
        }
    };
    try {
        Scene jump = Scene::mannequin();
        jump.name = "Motion tools / annotated jump";
        jump.last = 60;
        auto rest = jump.pose;
        for (auto key : std::vector<std::pair<int, float>>{
                 {0, 0}, {12, -.2f}, {24, .45f}, {36, .55f}, {48, -.1f}, {60, 0}}) {
            jump.pose = rest;
            jump.pose[0].t.setY(rest[0].t.y() + key.second);
            for (int n : {13, 17})
                jump.pose[n].r = QQuaternion::fromEulerAngles(key.second < 0 ? 25 : 0, 0, 0);
            jump.keys[key.first] = {jump.pose, {}, jump.morphs};
        }
        for (auto event :
             std::vector<QJsonObject>{note("Preparation", 0, .4, {0}), note("Takeoff", .4, .4, {15, 19}),
                                      note("Flight", .4, 1.6, {0}), note("Landing", 1.6, 2, {15, 19})})
            editAnnotations(jump, {{"operation", "add"}, {"annotation", event}});
        jump.evaluate(0);
        save("annotated-jump", jump);
        Scene curves = Scene::mannequin();
        curves.name = "Motion tools / interpolation and rotation";
        curves.last = 120;
        curves.fps = 30;
        curves.curveBasePose = curves.pose;
        ScalarCurve position;
        position.id = "demo-root-x";
        position.node = 0;
        position.path = "position";
        position.component = 0;
        position.keys = {{0, 0},     {.5, .2}, {1, .2},  {1.5, .45}, {2, .45},
                         {2.5, .65}, {3, .65}, {3.5, 0}, {4, 0}};
        QStringList modes{"Step", "Linear", "Bezier", "Hermite", "Bounce", "Elastic", "Back", "Bezier"};
        for (int i = 0; i < 8; ++i)
            position.keys[i].interpolation = modes[i];
        ScalarCurve spin;
        spin.id = "demo-winding";
        spin.path = "rotationEuler";
        spin.node = 4;
        spin.component = 1;
        spin.keys = {{0, 0}, {4, 720}};
        spin.keys[0].interpolation = "Linear";
        curves.curves = {position, spin};
        for (int i = 0; i < 8; ++i)
            editAnnotations(curves,
                            {{"operation", "add"},
                             {"annotation", note(modes[i], i * .5, (i + 1) * .5, {0}, "interpolation")}});
        curves.evaluate(0);
        save("curves-paths", curves);
        Scene volumes;
        volumes.name = "Motion tools / surface containment and allowed contact";
        volumes.nodes = {{"Torso volume", -1, {}, true}, {"Hand volume", -1, {}, true}};
        volumes.pose = volumes.restPose();
        volumes.last = 60;
        auto cube = [](int node, float radius, QColor color) {
            Mesh mesh;
            mesh.node = node;
            mesh.color = color;
            for (auto p : std::vector<QVector3D>{{-1, -1, -1},
                                                 {1, -1, -1},
                                                 {1, 1, -1},
                                                 {-1, 1, -1},
                                                 {-1, -1, 1},
                                                 {1, -1, 1},
                                                 {1, 1, 1},
                                                 {-1, 1, 1}}) {
                Vertex v;
                v.p = p * radius;
                v.p.setY(v.p.y() + 1);
                mesh.vertices.push_back(v);
            }
            mesh.indices = {0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4,
                            3, 7, 6, 3, 6, 2, 0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5};
            completeGeometryBasis(mesh);
            return mesh;
        };
        volumes.meshes = {cube(0, .4f, QColor(90, 140, 180)), cube(1, .12f, QColor(230, 150, 60))};
        volumes.pose[1].t = {1, 0, 0};
        volumes.keys[0] = {volumes.pose, {}, {}};
        volumes.pose[1].t = {0, 0, 0};
        volumes.keys[30] = {volumes.pose, {}, {}};
        volumes.pose[1].t = {1, 0, 0};
        volumes.keys[60] = {volumes.pose, {}, {}};
        editAnnotations(volumes, {{"operation", "add"},
                                  {"annotation", note("Authored touch exception; inspect interval", .55, .7,
                                                      {0, 1}, "allowed-contact")}});
        volumes.evaluate(0);
        save("penetration-and-contact", volumes);
        Scene target = Scene::mannequin();
        target.name = "Motion tools / different proportions";
        target.profile = target.suggestedProfile();
        target.profile.configured = true;
        auto old = target.globals(target.restPose());
        for (int n : {6, 7, 10, 11})
            target.nodes[n].rest.t *= 1.25f;
        for (int n : {14, 15, 18, 19})
            target.nodes[n].rest.t *= .8f;
        target.nodes[0].rest.t.setY(.868f);
        auto fresh = target.globals(target.restPose());
        for (auto &mesh : target.meshes) {
            for (auto &v : mesh.vertices) {
                int joint = mesh.joints[v.joints[0]];
                v.p = (fresh[joint] * old[joint].inverted()).map(v.p);
                v.normal = {};
            }
            for (size_t i = 0; i < mesh.joints.size(); ++i)
                mesh.inverseBind[i] = fresh[mesh.joints[i]].inverted();
            completeGeometryBasis(mesh);
        }
        target.pose = target.restPose();
        save("retarget-target", target);
        QJsonObject report;
        auto result =
            retargetMotion(jump, target, {{"fps", 30}, {"ik", true}, {"rootMotion", "scale"}}, report);
        save("retarget-result", result);
        QFile manifest(QDir(directory).filePath("manifest.json"));
        if (!manifest.open(QIODevice::WriteOnly))
            return 2;
        manifest.write(
            QJsonDocument(QJsonObject{{"license", "MIT; original synthetic geometry and motions"},
                                      {"scenes", files},
                                      {"retarget", report},
                                      {"surfacePairExample", QJsonArray{QJsonValue(QJsonArray{0, 1})}}})
                .toJson());
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }
}
