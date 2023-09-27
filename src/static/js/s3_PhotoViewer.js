/**
 * Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * This file is licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License. A copy of
 * the License is located at
 *
 * http://aws.amazon.com/apache2.0/
 *
 * This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 *
 */

// snippet-comment:[These are tags for the AWS doc team's sample catalog. Do not remove.]
// snippet-sourcedescription:[s3_PhotoViewer.js demonstrates how to allow viewing of photos in albums stored in an Amazon S3 bucket.]
// snippet-service:[s3]
// snippet-keyword:[JavaScript]
// snippet-sourcesyntax:[javascript]
// snippet-keyword:[Amazon S3]
// snippet-keyword:[Code Sample]
// snippet-sourcetype:[full-example]
// snippet-sourcedate:[2019-05-07]
// snippet-sourceauthor:[AWS-JSDG]

// ABOUT THIS JAVASCRIPT SAMPLE: This sample is part of the SDK for JavaScript Developer Guide topic at
// https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/s3-example-photos-view.html

// snippet-start:[s3.JavaScript.s3_PhotoViewer.complete]
//
// Data constructs and initialization.
//

// snippet-start:[s3.JavaScript.s3_PhotoViewer.config]
// **DO THIS**:
//   Replace BUCKET_NAME with the bucket name.
//
var albumBucketName = 'pengfei-lisanne-wedding';


// **DO THIS**:
//   Replace this block of code with the sample code located at:
//   Cognito -- Manage Identity Pools -- [identity_pool_name] -- Sample Code -- JavaScript
//
// Initialize the Amazon Cognito credentials provider
AWS.config.region = 'us-east-1'; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: 'us-east-1:24ead140-cea6-42c9-9f71-627eaa128239',
});

// Create a new service object
var s3 = new AWS.S3({
  apiVersion: '2006-03-01',
  params: {Bucket: albumBucketName}
});

// A utility function to create HTML.
function getHtml(template) {
  return template.join('\n');
}
// snippet-end:[s3.JavaScript.s3_PhotoViewer.config]


//
// Functions
//

// snippet-start:[s3.JavaScript.s3_PhotoViewer.listAlbums]
// List the photo albums that exist in the bucket.
function listAlbums() {
  s3.listObjects({Delimiter: '/'}, function(err, data) {
    if (err) {
      return alert('There was an error listing your albums: ' + err.message);
    } else {
      var albums = data.CommonPrefixes.map(function(commonPrefix) {
        var prefix = commonPrefix.Prefix;
        var albumName = decodeURIComponent(prefix.replace('/', ''));
        return getHtml([
          '<li>',
            '<button style="margin:5px;" onclick="viewAlbum(\'' + albumName + '\')">',
              albumName,
            '</button>',
          '</li>'
        ]);
      });
      var message = albums.length ?
        getHtml([
          '<p>Click on an album name to view it<點擊相簿名稱即可查看>.</p>',
        ]) :
        '<p>You do not have any albums. Please Create album.';
      var htmlTemplate = [
        '<h2>Albums<相簿></h2>',
        message,
        '<ul>',
          getHtml(albums),
        '</ul>',
      ]
      document.getElementById('viewer').innerHTML = getHtml(htmlTemplate);
    }
  });
}

function viewAlbum(albumName) {
  //var albumMediaKey = encodeURIComponent(albumName) + '/';
  var albumMediaKey = encodeURI(albumName) + '/';
  s3.listObjects({Prefix: albumMediaKey}, function(err, data) {
    if (err) {
      return alert('There was an error viewing your album: ' + err.message);
    }
    var href = this.request.httpRequest.endpoint.href; // https://s3.amazonaws.com/
    var bucketUrl = href + albumBucketName + '/';
    console.log('href:', href);
    console.log('bucketUrl:', bucketUrl);
    console.log('albumMediaKey:', albumMediaKey);
    console.log('data', data)
    console.log('data.Contents', data.Contents)
    var mediaHtml = data.Contents.map(function(media) {
      var mediaKey = media.Key;
      var mediaUrl = bucketUrl + encodeURIComponent(mediaKey);// s3:**/pengfei-wedding/folder/*.jpg
      var extension = mediaKey.split('.').pop().toLowerCase(); //jpg
      var mediaElement;
      console.log('albumMediaKey:', albumMediaKey);
      console.log('mediaUrl:', mediaUrl);

      if (extension === 'jpg' || extension === 'png' || extension === 'jpeg') {
        mediaElement = '<img src="' + mediaUrl + '" alt="' + mediaKey.replace(albumMediaKey, '') + '"/>';
      } else if (extension === 'mp4') {
        mediaElement = '<video controls><source src="' + mediaUrl + '" type="video/mp4"></video>';
      } else {
        mediaElement = '<p>Unsupported media type: ' + extension + '</p>';
      }

      return getHtml([
        '<span>',
          '<div>',
            '<br/>',
            mediaElement,
          '</div>',
          '<div>',
            '<span>',
              mediaKey.replace(albumMediaKey, ''),
            '</span>',
          '</div>',
        '</span>',
      ]);
    });

    var message = mediaHtml.length ?
      '<p>The following media files are present.</p>' :
      '<p>There are no media files in this album.</p>';

    var htmlTemplate = [
      '<div>',
        '<button onclick="listAlbums()">',
          'Back To Albums(返回相冊)',
        '</button>',
      '</div>',
      '<h2>',
        'Album: ' + albumName,
      '</h2>',
      message,
      '<div>',
        getHtml(mediaHtml),
      '</div>',
      '<h2>',
        'End of Album: ' + albumName,
      '</h2>',
      '<div>',
        '<button onclick="listAlbums()">',
          'Back To Albums(返回相冊)',
        '</button>',
      '</div>',
    ]
    document.getElementById('viewer').innerHTML = getHtml(htmlTemplate);
  });
}
// snippet-end:[s3.JavaScript.s3_PhotoViewer.viewAlbum]
// snippet-end:[s3.JavaScript.s3_PhotoViewer.complete]
