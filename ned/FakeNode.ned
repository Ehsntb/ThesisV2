// /ned/FakeNode.ned

package ned;

simple FakeNode
{
    parameters:
        @class(::FakeNode);
        @display("i=block/process");

        bool   enabled        = default(true);
        int    attackMode     = default(1);          // 1 = replay
        double replayInterval @unit(s) = default(2.5s);

        // بسته پایه برای بازپخش
        int    replayId       = default(100000);
        int    replayTsUs     = default(500000);     // microseconds
        string replayTagHex   = default("00000000000000000000000000000000");

        // مک معتبر (CMAC با کلید مشترک)
        bool   validMac       = default(false);
        string aesKeyHex      = default("00112233445566778899AABBCCDDEEFF");

        // شدت حمله: تکرار مشروع + بی‌نظمی زمان رسیدن
        int    dupBurstLen    = default(0);          // تعداد کپی اضافه (فراتر از اولین پیام)
        double dupBurstGap @unit(s) = default(1s);   // فاصله بین کپی‌ها در برست
        double outOfOrderJitter @unit(s) = default(0s); // تاخیر تصادفی هر کپی برای خارج از ترتیب
    gates:
        output out;
}