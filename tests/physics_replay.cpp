#include "physics_replay.h"
#include <QCoreApplication>
#include <QFile>
#include <QJsonDocument>
#include <QTextStream>
int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    if (argc < 2) {
        QTextStream(stderr) << "Usage: TricksterPhysicsReplay report.json|project.trickster ...\n";
        return 2;
    }
    bool ok = true;
    for (int i = 1; i < argc; ++i) {
        QFile f(QString::fromLocal8Bit(argv[i]));
        if (!f.open(QIODevice::ReadOnly)) {
            QTextStream(stderr) << f.errorString() << '\n';
            return 2;
        }
        auto obj = QJsonDocument::fromJson(f.readAll()).object();
        if (obj.contains("physicsResult"))
            obj = obj["physicsResult"].toObject();
        QJsonObject result;
        QString error;
        bool passed = trickster::verifyControlReplay(obj, result, error);
        result["passed"] = passed;
        result["error"] = error;
        result["input"] = QString::fromLocal8Bit(argv[i]);
        QTextStream(stdout) << QJsonDocument(result).toJson(QJsonDocument::Compact) << '\n';
        ok &= passed;
    }
    return ok ? 0 : 1;
}
