// 生成演示小票图片（macOS Swift + AppKit，无第三方依赖）。
// 用途：为正式 API 测试准备文字清晰、OCR 可辨识的小票/支付截图。
// 运行：swift demo_data/make_demo_receipts.swift [输出目录]
// 输出：demo_data/receipt_*.png（覆盖餐饮、购物、支付截图三类）
import AppKit
import Foundation

let outputDir = CommandLine.arguments.count > 1
    ? CommandLine.arguments[1]
    : FileManager.default.currentDirectoryPath

struct Receipt {
    let filename: String
    let title: String
    let subtitle: String
    let lines: [(String, String)]
    let total: String
    let date: String
    let footer: String
}

let receipts = [
    Receipt(
        filename: "receipt_coffee.png",
        title: "星巴克咖啡",
        subtitle: "STARBUCKS COFFEE 中关村店",
        lines: [
            ("拿铁 (中杯)", "28.00"),
            ("服务费等", "0.00"),
        ],
        total: "28.00",
        date: "2026-11-16  14:32",
        footer: "支付方式：微信支付  感谢惠顾"
    ),
    Receipt(
        filename: "receipt_market.png",
        title: "盒马鲜生",
        subtitle: "HEMA FRESH 会员店",
        lines: [
            ("有机蔬菜 x2", "36.00"),
            ("鲜牛奶 x1", "18.50"),
            ("鸡蛋 x1", "12.00"),
        ],
        total: "66.50",
        date: "2026-11-15  18:05",
        footer: "支付方式：支付宝  会员积分 +66"
    ),
    Receipt(
        filename: "receipt_payment.png",
        title: "支付宝付款成功",
        subtitle: "滴滴出行 - 快车",
        lines: [
            ("行程费用", "32.50"),
            ("优惠减免", "-5.00"),
        ],
        total: "27.50",
        date: "2026-11-14  21:47",
        footer: "交易单号 2026111421470001  已支付"
    ),
]

let W = 480
let H = 720

func drawReceipt(_ r: Receipt) {
    // 用 flipped NSImage 画布：原点左上，符合文本直觉
    let image = NSImage(size: NSSize(width: W, height: H))
    image.lockFocus()

    let ctx = NSGraphicsContext.current!.cgContext

    // 白底
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))

    // 虚线外框（flipped 下 y 从顶部算）
    let pad: CGFloat = 20
    ctx.setStrokeColor(CGColor(red: 0.15, green: 0.15, blue: 0.15, alpha: 1))
    ctx.setLineWidth(2)
    ctx.stroke(CGRect(x: pad, y: pad, width: CGFloat(W) - 2 * pad, height: CGFloat(H) - 2 * pad))

    func font(_ size: CGFloat, bold: Bool) -> NSFont {
        NSFont(name: bold ? "PingFangSC-Semibold" : "PingFangSC-Regular", size: size)
            ?? NSFont.systemFont(ofSize: size, weight: bold ? .semibold : .regular)
    }
    func draw(_ s: String, x: CGFloat, y: CGFloat, size: CGFloat, bold: Bool = false, align: NSTextAlignment = .left, w: CGFloat) {
        let style = NSMutableParagraphStyle()
        style.alignment = align
        let attrs: [NSAttributedString.Key: Any] = [
            .font: font(size, bold: bold),
            .foregroundColor: NSColor.black,
            .paragraphStyle: style,
        ]
        // lockFocus 坐标系原点在左下；把「从顶部算的 y」转换为底部语义
        let bottomY = CGFloat(H) - y - (size + 10)
        NSAttributedString(string: s, attributes: attrs)
            .draw(in: CGRect(x: x, y: bottomY, width: w, height: size + 10))
    }

    let innerPad: CGFloat = 40
    let contentW = CGFloat(W) - 2 * innerPad
    var y: CGFloat = 60
    draw(r.title, x: innerPad, y: y, size: 28, bold: true, align: .center, w: contentW); y += 42
    draw(r.subtitle, x: innerPad, y: y, size: 14, align: .center, w: contentW); y += 26

    // 分隔线（flipped 坐标系：直接 y）
    func separator(at yy: CGFloat) {
        let bottomY = CGFloat(H) - yy
        ctx.setLineWidth(1)
        ctx.setStrokeColor(CGColor(red: 0.5, green: 0.5, blue: 0.5, alpha: 1))
        ctx.move(to: CGPoint(x: innerPad, y: bottomY))
        ctx.addLine(to: CGPoint(x: CGFloat(W) - innerPad, y: bottomY))
        ctx.strokePath()
    }
    separator(at: y); y += 22

    for (name, price) in r.lines {
        draw(name, x: innerPad, y: y, size: 17, w: contentW * 0.7)
        draw(price, x: innerPad + contentW * 0.7, y: y, size: 17, align: .right, w: contentW * 0.3)
        y += 32
    }

    y += 8
    separator(at: y); y += 18

    draw("合计", x: innerPad, y: y, size: 22, bold: true, w: contentW * 0.4)
    draw("¥ " + r.total, x: innerPad + contentW * 0.4, y: y, size: 26, bold: true, align: .right, w: contentW * 0.6)
    y += 52

    separator(at: y); y += 18
    draw(r.date, x: innerPad, y: y, size: 15, align: .center, w: contentW); y += 30
    draw(r.footer, x: innerPad, y: y, size: 13, align: .center, w: contentW)

    image.unlockFocus()

    guard let tiff = image.tiffRepresentation,
          let rep = NSBitmapImageRep(data: tiff),
          let png = rep.representation(using: .png, properties: [:]) else { return }
    let url = URL(fileURLWithPath: outputDir).appendingPathComponent(r.filename)
    try? png.write(to: url)
    print("生成: \(url.path)")
}

for r in receipts { drawReceipt(r) }
print("完成，共 \(receipts.count) 张小票图")
