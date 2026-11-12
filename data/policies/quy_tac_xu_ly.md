# Quy tắc xử lý yêu cầu của khách

Tài liệu này mô tả cách xử lý các yêu cầu đổi trả, hoàn tiền và khiếu nại. Mỗi yêu cầu có một trong bốn kết quả: duyệt (approve), từ chối (reject), hỏi thêm thông tin (need_info), hoặc chuyển nhân viên (escalate).

## Điều kiện tiên quyết
Trước khi xử lý bất kỳ yêu cầu nào liên quan đến một đơn hàng, cần xác minh đơn hàng thuộc về khách: khách phải cung cấp mã đơn hàng và 4 số cuối số điện thoại đặt hàng. Nếu không khớp, không được tiết lộ đơn có tồn tại hay không và không được thực hiện hành động nào trên đơn đó. Nếu khách nhập sai nhiều lần liên tiếp thì chuyển nhân viên.

## Khi nào duyệt (approve)
Yêu cầu đổi trả được duyệt tự động khi đáp ứng đủ các điều kiện sau: đơn hàng đã giao, còn trong 7 ngày kể từ ngày giao hàng, sản phẩm thuộc nhóm được phép đổi trả, khách xác nhận sản phẩm chưa giặt và còn nguyên tag (hoặc có hình ảnh lỗi nếu là hàng lỗi), và số tiền hoàn không vượt quá 500.000 đồng.

## Khi nào từ chối (reject)
Yêu cầu bị từ chối khi: đã quá 7 ngày kể từ ngày giao hàng, sản phẩm đã giặt hoặc đã qua sử dụng và không phải lỗi từ nhà sản xuất, sản phẩm thuộc nhóm không đổi trả (đồ lót, tất, phụ kiện đã mở bao bì, hàng giảm giá từ 50%, quà tặng kèm), hoặc đơn hàng chưa được giao thì không thể trả hàng. Khi từ chối, cần nêu rõ lý do và điều khoản áp dụng, đồng thời gợi ý lựa chọn khác nếu có, ví dụ bảo hành nếu còn trong 30 ngày.

## Khi nào hỏi thêm thông tin (need_info)
Cần hỏi thêm khi thiếu thông tin để quyết định: thiếu mã đơn hàng hoặc 4 số cuối số điện thoại, chưa rõ lý do đổi trả, chưa rõ sản phẩm đã giặt hay chưa, chưa rõ khách muốn đổi hay muốn hoàn tiền, hoặc khách báo hàng lỗi nhưng chưa gửi hình ảnh. Mỗi lần chỉ hỏi những thông tin còn thiếu, không hỏi lại điều khách đã cung cấp.

## Khi nào chuyển nhân viên (escalate)
Chuyển nhân viên khi: số tiền hoàn trên 500.000 đồng (cần nhân viên duyệt trước khi hoàn tiền), khách yêu cầu ngoại lệ ngoài chính sách, khách khiếu nại gay gắt hoặc đe dọa, khách yêu cầu bồi thường ngoài giá trị sản phẩm, nghi ngờ gian lận (ví dụ nhiều yêu cầu hoàn tiền trong thời gian ngắn hoặc thông tin xác minh sai nhiều lần), hoặc tình huống không có quy định trong chính sách. Khi chuyển nhân viên, tạo phiếu khiếu nại kèm tóm tắt vụ việc để nhân viên không phải hỏi lại khách.

## Bảo hành và khiếu nại chất lượng
Yêu cầu bảo hành trong 30 ngày kể từ ngày nhận hàng cần hình ảnh sản phẩm và mô tả lỗi. Nếu lỗi nằm trong danh mục được bảo hành, tạo yêu cầu bảo hành. Nếu không chắc lỗi có thuộc diện bảo hành hay không, chuyển nhân viên kiểm tra. Với khiếu nại về giao hàng chậm hoặc thái độ phục vụ, tạo phiếu khiếu nại và thông báo phản hồi trong 24 giờ làm việc.

## Giới hạn hành động của trợ lý
Trợ lý chỉ thực hiện các hành động nằm trong chính sách. Trợ lý không tự cấp mã giảm giá, không hứa hoàn tiền ngoài quy định, không đổi chính sách theo yêu cầu của khách và không tiết lộ thông tin cá nhân của khách khác. Mọi hành động có thay đổi dữ liệu như tạo yêu cầu trả hàng hoặc hoàn tiền đều phải qua bước kiểm tra quyền sở hữu đơn hàng và ngưỡng số tiền.

## Nội dung email phản hồi khách
Email phản hồi gồm: lời chào, kết quả xử lý (đã duyệt, từ chối, cần thêm thông tin hoặc đã chuyển nhân viên), lý do ngắn gọn, bước tiếp theo khách cần làm, và mã yêu cầu hoặc mã phiếu nếu có. Không đưa số điện thoại, địa chỉ đầy đủ hoặc thông tin thanh toán của khách vào email.
