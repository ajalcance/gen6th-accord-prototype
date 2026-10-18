# QR share encoder attribution

`frontend/lib/passport-qr.ts` implements the bounded version 8 / low correction / mask 0
byte-mode subset, informed by [Project Nayuki's reference](https://www.nayuki.io/page/qr-code-generator-library).
No package was installed. Preserve this notice in the reviewed submission inventory.
Independent matrix fixtures use the already bundled ReportLab encoder; neither library is
a production runtime dependency. Phone-camera/rendered scanning remains separate acceptance.

Copyright (c) Project Nayuki. (MIT License)
https://www.nayuki.io/page/qr-code-generator-library

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

- The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
- The Software is provided "as is", without warranty of any kind, express or
  implied, including but not limited to the warranties of merchantability,
  fitness for a particular purpose and noninfringement. In no event shall the
  authors or copyright holders be liable for any claim, damages or other
  liability, whether in an action of contract, tort or otherwise, arising from,
  out of or in connection with the Software or the use or other dealings in the
  Software.
