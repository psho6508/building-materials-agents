// 구글 Apps Script 웹앱 — GitHub Actions가 서비스 계정 대신 이 웹앱을 통해
// 본인(psho6508) 계정 권한으로 구글 드라이브에 문서를 저장하게 한다.
// (서비스 계정은 저장용량이 0GB라 개인 Gmail 드라이브에 새 파일을 못 만든다 —
//  이 웹앱은 배포한 사람의 권한으로 실행되므로 그 문제가 없다.)
//
// 설정:
// 1. script.google.com → 새 프로젝트 → 이 코드 붙여넣기
// 2. 프로젝트 설정(톱니바퀴) → 스크립트 속성 → 속성 추가:
//    이름 SHARED_SECRET, 값은 GitHub Secrets의 APPS_SCRIPT_SECRET과 동일한 값으로
//    (이 .gs 파일은 공개 저장소에 커밋되므로 비밀값을 코드에 직접 적지 않는다)
// 3. 배포 → 새 배포 → 유형: 웹 앱 → 실행 대상: 나 → 액세스 권한: 모든 사용자 → 배포
//    처음 배포 시 권한 승인 화면이 뜨면 본인 계정으로 승인
//    (고급 → 안전하지 않음으로 이동, 눌러도 됨 — 본인이 만든 스크립트이므로 안전)

function doPost(e) {
  var SHARED_SECRET = PropertiesService.getScriptProperties().getProperty("SHARED_SECRET");

  var data = JSON.parse(e.postData.contents);
  if (data.secret !== SHARED_SECRET) {
    return ContentService.createTextOutput(JSON.stringify({ error: "unauthorized" }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var folder = DriveApp.getFolderById(data.folderId);
    var doc = DocumentApp.create(data.title);
    var body = doc.getBody();
    body.setText(data.text);
    doc.saveAndClose();

    var file = DriveApp.getFileById(doc.getId());
    folder.addFile(file);
    DriveApp.getRootFolder().removeFile(file);

    return ContentService.createTextOutput(JSON.stringify({ url: doc.getUrl() }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
