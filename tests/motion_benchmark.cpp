#include "appearance.h"
#include "trickster_version.h"
#include "window.h"
#include <QApplication>
#include <QBuffer>
#include <QCryptographicHash>
#include <QElapsedTimer>
#include <QEventLoop>
#include <QFile>
#include <QImage>
#include <QJsonDocument>
#include <QOpenGLContext>
#include <QOpenGLFunctions>
#include <QScreen>
#include <QSettings>
#include <QSysInfo>
#include <QThread>
#include <QTimer>
#include <algorithm>
#include <cmath>
#include <numeric>
#ifdef Q_OS_WIN
#include <qt_windows.h>

#include <psapi.h>
#endif
using namespace trickster;
QJsonObject distribution(std::vector<double> values) {
    if (values.empty())
        return {};
    double sum = std::accumulate(values.begin(), values.end(), 0.);
    std::sort(values.begin(), values.end());
    auto p = [&](double f) {
        return values[std::min(values.size() - 1, size_t(std::ceil(f * values.size()) - 1))];
    };
    return {{"mean", sum / values.size()},
            {"p95", p(.95)},
            {"p99", p(.99)},
            {"max", values.back()},
            {"samples", int(values.size())}};
}
Scene fixture(QString kind) {
    Scene s = Scene::mannequin();
    s.name = kind;
    s.profile = s.suggestedProfile();
    s.profile.configured = true;
    if (kind == "dense-textured" || kind == "morph") {
        auto &m = s.meshes[0];
        auto vertices = m.vertices;
        auto indices = m.indices;
        int copies = kind == "dense-textured" ? 32 : 8;
        for (int copy = 1; copy < copies; ++copy) {
            unsigned base = unsigned(m.vertices.size());
            for (auto v : vertices) {
                v.p += QVector3D(0, 0, float(copy) * .00001f);
                m.vertices.push_back(v);
            }
            for (auto i : indices)
                m.indices.push_back(base + i);
        }
        QImage image(512, 512, QImage::Format_RGBA8888);
        image.fill(QColor(120, 150, 180));
        Texture t;
        QBuffer bytes(&t.bytes);
        bytes.open(QIODevice::WriteOnly);
        image.save(&bytes, "PNG");
        m.textures["baseColor"] = t;
        for (auto &v : m.vertices) {
            int original = v.joints[0];
            for (int k = 0; k < 8; ++k) {
                v.joints[k] = (original+k)%int(m.joints.size());
                v.weights[k] = .125f;
            }
        }
        if (kind == "morph") {
            MorphTarget target;
            target.positions.resize(m.vertices.size(), {.02f, .01f, 0});
            target.normals.resize(m.vertices.size(), {.01f, 0, .01f});
            m.targets = {target};
            m.node = 0;
            s.nodes[0].morphRest = {0};
            s.morphs[0] = {0};
        }
    }
    if (kind == "different-proportions") {
        for (auto &n : s.nodes)n.rest.t *= 1.3f;
        s.pose = s.restPose();auto bind=s.globals(s.pose);
        for(auto &mesh:s.meshes){for(auto &vertex:mesh.vertices)vertex.p*=1.3f;
            for(size_t j=0;j<mesh.joints.size();++j)mesh.inverseBind[j]=bind[mesh.joints[j]].inverted();}
    }
    s.keys[0] = {s.pose, {}, s.morphs};
    s.pose[6].r = QQuaternion::fromEulerAngles(0, 0, -45);
    s.pose[10].r = QQuaternion::fromEulerAngles(0, 0, 45);
    s.keys[30] = {s.pose, {}, s.morphs};
    if (kind == "morph")
        s.keys[30].morphs[0] = {1};
    s.last = 60;
    s.keys[60] = s.keys[0];
    if (kind == "long-baked") {
        auto source = s.motionOnlyCopy();
        s.keys.clear();
        s.last = 3600;
        for (int f = 0; f <= s.last; ++f) {
            source.evaluate(float(f % 60));
            s.keys[f] = {source.pose, source.pins, source.morphs};
        }
    }
    if (kind == "layers-ik-contacts") {
        QString error;
        s.evaluate(0);
        s.beginCorrection(0, 60, 0, 0, false, error);
        s.layers[0].id = "benchmark-layer";
        for(int layer=0;layer<3;++layer){if(layer)s.layers.push_back(s.layers.front());auto &correction=s.layers[layer];correction.id=QString("benchmark-layer-%1").arg(layer);correction.name=correction.id;
            for(int frame=0;frame<=60;++frame)for(int n:{1,2,6,7,8,10,11,12}){Transform offset;offset.s={0,0,0};offset.r=QQuaternion::fromEulerAngles(0,0,float(std::sin(frame*.1+layer)*2));correction.keys[frame].offsets[n]=offset;correction.keys[frame].channels[n]=2;}}
        s.contacts.push_back({15, 0, 60, s.positions(s.pose)[15], s.defaultPole(15)});
    }
    s.evaluate(0);
    return s;
}
int main(int argc, char **argv) {
    QSurfaceFormat format;
    format.setVersion(2, 1);
    format.setProfile(QSurfaceFormat::CompatibilityProfile);
    format.setDepthBufferSize(24);
    QSurfaceFormat::setDefaultFormat(format);
    QApplication app(argc, argv);
    app.setApplicationName("TricksterMotionBenchmark");
    app.setOrganizationName("TricksterTests");
    QSettings().clear();
    applyAppearance(app);
    Window w;
    w.resize(qRound(1920 / w.devicePixelRatioF()), qRound(1080 / w.devicePixelRatioF()));
    w.show();
    QApplication::processEvents();
    QJsonArray cases;
    for (QString name :
         {"simple", "dense-textured", "morph", "long-baked", "layers-ik-contacts", "different-proportions"}) {
        if(argc>2&&name!=QString::fromLocal8Bit(argv[2]))continue;
        auto scene=fixture(name);
        int requestedFps=argc>3?QString::fromLocal8Bit(argv[3]).toInt():30;
        if(requestedFps!=30&&requestedFps!=60)return 3;
        if(requestedFps!=scene.fps){int ratio=requestedFps/scene.fps;QMap<int,Key> keys;for(auto k=scene.keys.cbegin();k!=scene.keys.cend();++k)keys[k.key()*ratio]=k.value();scene.keys=keys;scene.first*=ratio;scene.last*=ratio;
            for(auto &contact:scene.contacts){contact.first*=ratio;contact.last*=ratio;contact.fadeIn*=ratio;contact.fadeOut*=ratio;}
            for(auto &layer:scene.layers){QMap<int,CorrectionKey> keys;for(auto k=layer.keys.cbegin();k!=layer.keys.cend();++k)keys[k.key()*ratio]=k.value();layer.keys=keys;layer.first*=ratio;layer.last*=ratio;layer.fadeIn*=ratio;layer.fadeOut*=ratio;}
            scene.fps=requestedFps;scene.evaluate(0);
        }
        w.document().replace(std::move(scene));
        auto inputHash = QString::fromLatin1(
            QCryptographicHash::hash(
                QJsonDocument(sceneToJson(w.document().scene)).toJson(QJsonDocument::Compact),
                QCryptographicHash::Sha256)
                .toHex());
        w.document().select(6);
        w.viewport->fit();
        for (bool cpu : {true, false}) {
            w.viewport->forceCpuSkinning = cpu;
            QMap<QString, std::vector<double>> times;
            QElapsedTimer elapsed;
            elapsed.start();
            int swaps = 0;
            auto connection =
                QObject::connect(w.viewport, &QOpenGLWidget::frameSwapped, &w, [&] { ++swaps; });
            for (int i = -20; i < 100; ++i) {
                auto before = w.viewport->renderingStats();
                QElapsedTimer sample;
                sample.start();
                w.document().seek((i + 20) % 60);
                double seek = sample.nsecsElapsed() / 1e6;
                QApplication::processEvents();
                w.viewport->grabFramebuffer();
                QApplication::processEvents();
                if (i < 0)
                    continue;
                auto stats = w.viewport->renderingStats();
                auto &s = w.document().scene;
                times["seekIncludingPanels"].push_back(seek);
                times["sourceEvaluation"].push_back(s.sourceEvaluationMs);
                times["curveEvaluation"].push_back(s.curveEvaluationMs);
                times["layerEvaluation"].push_back(s.layerEvaluationMs);
                times["constraints"].push_back(s.constraintEvaluationMs);
                times["panelRefresh"].push_back(w.lastPanelRefreshMs);
                times["timelinePaint"].push_back(w.timeline->lastPaintMs);
                times["cpuSkinPerIteration"].push_back(stats["totalCpuSkinMs"].toDouble() -
                                                       before["totalCpuSkinMs"].toDouble());
                times["uploadPerIteration"].push_back(stats["totalUploadMs"].toDouble() -
                                                      before["totalUploadMs"].toDouble());
                times["paintCpuPerIteration"].push_back(stats["totalPaintCpuMs"].toDouble() -
                                                        before["totalPaintCpuMs"].toDouble());
                for (auto field : {"gpuDrawMs"})
                    if (stats[field].isDouble())
                        times[field].push_back(stats[field].toDouble());
                times["frameReadbackEndToEnd"].push_back(sample.nsecsElapsed() / 1e6);
            }
            w.document().seek(0);
            w.document().play(true);
            QEventLoop playback;
            QTimer::singleShot(2000, &playback, &QEventLoop::quit);
            playback.exec();
            w.document().play(false);
            QApplication::processEvents();
            QObject::disconnect(connection);
            QJsonObject result{{"fixture", name},
                               {"forcedCpu", cpu},
                               {"elapsedMs", double(elapsed.elapsed())},
                               {"presentedSwapsIncludingWarmup", swaps},
                               {"measuredIterations", 100},
                               {"warmupIterations", 20},
                               {"playbackDroppedFrames", QJsonValue()},
                               {"frameCountMeaning",
                                "Explicit seek/readback benchmark; playback frame dropping was not measured"},
                               {"renderer", w.viewport->renderingStats()}};
            QJsonObject metrics;
            for (auto it = times.begin(); it != times.end(); ++it)
                metrics[it.key()] = distribution(it.value());
            result["playback"] = w.document().playbackStats();
            result.remove("playbackDroppedFrames");
            result["frameCountMeaning"] = "Explicit seek/readback timing followed by separate 2-second real "
                                          "Qt playback; Qt frameSwapped counts unique playback ordinals";
            result["milliseconds"] = metrics;
            qint64 vertices = 0, indices = 0;
            for (auto &mesh : w.document().scene.meshes) {
                vertices += mesh.vertices.size();
                indices += mesh.indices.size();
            }
            result["inputSha256"] = inputHash;
            result["vertices"] = vertices;
            result["indices"] = indices;
            result["nodes"] = int(w.document().scene.nodes.size());
            result["fps"]=w.document().scene.fps;
            cases.append(result);
        }
    }
    QJsonObject report{{"version", TRICKSTER_VERSION},
                       {"build", TRICKSTER_BUILD_ID},
                       {"os", QSysInfo::prettyProductName()},
                       {"cpuArchitecture", QSysInfo::currentCpuArchitecture()},
                       {"logicalProcessors", QThread::idealThreadCount()},
                       {"qt", QT_VERSION_STR},
                       {"windowLogical", QJsonArray{w.width(), w.height()}},
                       {"devicePixelRatio", w.devicePixelRatioF()},
                       {"viewportPhysical", QJsonArray{qRound(w.viewport->width() * w.devicePixelRatioF()),
                                                       qRound(w.viewport->height() * w.devicePixelRatioF())}},
                       {"cases", cases},
                       {"comparison", "Controlled CPU fallback versus GPU path in the same dirty build, not "
                                      "a measurement of historical commit 39bee67"}};
    w.viewport->makeCurrent();
    auto context = w.viewport->context();
    report["glVendor"] =
        QString(reinterpret_cast<const char *>(context->functions()->glGetString(GL_VENDOR)));
    report["glRenderer"] =
        QString(reinterpret_cast<const char *>(context->functions()->glGetString(GL_RENDERER)));
    report["glVersion"] =
        QString(reinterpret_cast<const char *>(context->functions()->glGetString(GL_VERSION)));
    w.viewport->doneCurrent();
#ifdef Q_OS_WIN
    QSettings cpuRegistry("HKEY_LOCAL_MACHINE\\HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0",
                          QSettings::NativeFormat);
    report["cpuName"] = cpuRegistry.value("ProcessorNameString").toString();
    MEMORYSTATUSEX installedMemory{};
    installedMemory.dwLength = sizeof(installedMemory);
    GlobalMemoryStatusEx(&installedMemory);
    report["physicalMemoryGiB"] = double(installedMemory.ullTotalPhys) / 1073741824.;
    PROCESS_MEMORY_COUNTERS memory{};
    GetProcessMemoryInfo(GetCurrentProcess(), &memory, sizeof(memory));
    report["peakProcessMiB"] = double(memory.PeakWorkingSetSize) / 1048576;
#endif
    QString path = argc > 1 ? QString::fromLocal8Bit(argv[1]) : "artifacts/motion-performance.json";
    QFile file(path);
    if (!file.open(QIODevice::WriteOnly))
        return 2;
    file.write(QJsonDocument(report).toJson());
    w.document().undo.setClean();
    return 0;
}
