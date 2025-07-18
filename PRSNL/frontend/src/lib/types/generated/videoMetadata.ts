/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */
import type { VideoMetadataWidth } from './videoMetadataWidth';
import type { VideoMetadataHeight } from './videoMetadataHeight';
import type { VideoMetadataViewCount } from './videoMetadataViewCount';
import type { VideoMetadataLikeCount } from './videoMetadataLikeCount';
import type { VideoMetadataUploadDate } from './videoMetadataUploadDate';
import type { VideoMetadataCodec } from './videoMetadataCodec';
import type { VideoMetadataAudioCodec } from './videoMetadataAudioCodec';
import type { VideoMetadataAverageBitrate } from './videoMetadataAverageBitrate';
import type { VideoMetadataFilesize } from './videoMetadataFilesize';

export interface VideoMetadata {
  width?: VideoMetadataWidth;
  height?: VideoMetadataHeight;
  view_count?: VideoMetadataViewCount;
  like_count?: VideoMetadataLikeCount;
  upload_date?: VideoMetadataUploadDate;
  codec?: VideoMetadataCodec;
  audio_codec?: VideoMetadataAudioCodec;
  average_bitrate?: VideoMetadataAverageBitrate;
  filesize?: VideoMetadataFilesize;
}
