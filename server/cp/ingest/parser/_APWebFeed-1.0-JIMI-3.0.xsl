<?xml version='1.0'?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:apcm="http://ap.org/schemas/03/2005/apcm" xmlns:apnm="http://ap.org/schemas/03/2005/apnm"
  xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:cp="urn:schemas-cp-org:cp"
  exclude-result-prefixes="atom apcm apnm">

  <xsl:import href="CP-1.0-Regex.xslt" />
  <xsl:import href="CP-1.0-ANPA.xsl" />
  <xsl:import href="CP-1.0-Strings.xsl" />

  <xsl:output method="xml" encoding="utf-8" indent="yes" />

  <msxsl:script language="CSharp" implements-prefix="cp">
    <msxsl:using namespace="System.Globalization" />
    <msxsl:using namespace="System.Text.RegularExpressions" />
    <![CDATA[
	public static String ToUpperCase_MatchEvaluator(Match match)
	{
		return match.Value.ToUpper();
	}

	public static String STR_ProperCaseName(String input)
	{
		input = input.ToLower();

		//input = CultureInfo.InvariantCulture.TextInfo.ToTitleCase(input);

		input = Regex.Replace(input, "((?<![a-z])|(?<=mc|mac))[a-z]", ToUpperCase_MatchEvaluator);

		return input;
	}
]]>
  </msxsl:script>

  <xsl:template match="/">
    <!-- Atom Entry Document. -->
    <xsl:apply-templates select="atom:entry" />
  </xsl:template>

  <!-- Atom Entry Document -->
  <xsl:template match="atom:entry">
    <xsl:variable name="m_BizObjectClass">
      <xsl:choose>
        <xsl:when test="apcm:ContentMetadata/apcm:MediaType='Audio'">
          <xsl:text>Nstein.Ncm.Bll.Audio</xsl:text>
        </xsl:when>
        <xsl:when test="apcm:ContentMetadata/apcm:MediaType='Graphic'">
          <xsl:text>Nstein.Ncm.Bll.Photo</xsl:text>
        </xsl:when>
        <xsl:when test="apcm:ContentMetadata/apcm:MediaType='Photo'">
          <xsl:text>Nstein.Ncm.Bll.Photo</xsl:text>
        </xsl:when>
        <xsl:when test="apcm:ContentMetadata/apcm:MediaType='Video'">
          <xsl:text>Nstein.Ncm.Bll.Video</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>Nstein.Ncm.Bll.Article</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <!-- Extended Headline Value, Post Processing -->
    <xsl:variable name="m_HeadlineExtended">
      <xsl:call-template name="ProcessHeadline">
        <xsl:with-param name="Value" select="apcm:ContentMetadata/apcm:OriginalHeadLine" />
      </xsl:call-template>
    </xsl:variable>

    <!-- Short Headline Value, Post Processing -->
    <xsl:variable name="m_HeadlineShort">
      <xsl:call-template name="ProcessHeadline">
        <xsl:with-param name="Value" select="apcm:ContentMetadata/apcm:OriginalHeadLine" />
      </xsl:call-template>
    </xsl:variable>

    <!-- ManagementId is like NewsItemId -->
    <xsl:variable name="m_ManagementId" select="substring-after(apnm:NewsManagement/apnm:ManagementId, 'ap.org:')" />
    <!-- EntryId is like ContentItemId -->
    <xsl:variable name="m_EntryId" select="substring-after(atom:id, 'ap.org:')" />
    <!-- Count number audio, graphic, photo, and video in nitf body. -->
    <xsl:variable name="m_AudioCount">
      <xsl:choose>
        <xsl:when test="atom:content/nitf/body/body.content/media[@media-type='Audio']">
          <xsl:value-of select="count(atom:content/nitf/body/body.content/media[@media-type='Audio'])" />
        </xsl:when>
        <xsl:when test="atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Audio']">
          <xsl:value-of
            select="count(atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Audio'])" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="m_GraphicCount">
      <xsl:choose>
        <xsl:when test="atom:content/nitf/body/body.content/media[@media-type='Graphic']">
          <xsl:value-of select="count(atom:content/nitf/body/body.content/media[@media-type='Graphic'])" />
        </xsl:when>
        <xsl:when test="atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Graphic']">
          <xsl:value-of
            select="count(atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Graphic'])" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="m_PhotoCount">
      <xsl:choose>
        <xsl:when test="atom:content/nitf/body/body.content/media[@media-type='Photo']">
          <xsl:value-of select="count(atom:content/nitf/body/body.content/media[@media-type='Photo'])" />
        </xsl:when>
        <xsl:when test="atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Photo']">
          <xsl:value-of
            select="count(atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Photo'])" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="m_VideoCount">
      <xsl:choose>
        <xsl:when test="atom:content/nitf/body/body.content/media[@media-type='Video']">
          <xsl:value-of select="count(atom:content/nitf/body/body.content/media[@media-type='Video'])" />
        </xsl:when>
        <xsl:when test="atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Video']">
          <xsl:value-of
            select="count(atom:content/atom:nitf/atom:body/atom:body.content/atom:media[@media-type='Video'])" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="m_SlugLine" select="cp:REGEX_Replace(translate(atom:title, ' ', '-'), '-{2}', '-')" />
    <!-- Eds notes without Eds: or APNewsNow. -->
    <!--<xsl:variable name="m_Eds" select="cp:REGEX_Replace(cp:REGEX_Replace(apnm:NewsManagement/apnm:PublishingSpecialInstructions, '(?i)eds:\s*', ''), '(?i)APNewsNow[;.]?\s*', '')" />-->
    <xsl:variable name="m_Eds"
      select="cp:REGEX_Replace(apnm:NewsManagement/apnm:PublishingSpecialInstructions, '(?i)eds:\s*', '')" />
    <xsl:variable name="m_APNewsNow" select="cp:REGEX_Match($m_Eds, '(?i)APNewsNow[;.]?')" />
    <xsl:variable name="m_MovingOn" select="cp:REGEX_Match($m_Eds, 'Moving on.*\.')" />
    <!-- BEGIN ROOT ELEMENT -->
    <xsl:element name="BizObject">
      <xsl:attribute name="Class">
        <xsl:value-of select="$m_BizObjectClass" />
      </xsl:attribute>
      <xsl:element name="Relations" />
      <xsl:element name="SemanticData" />
      <xsl:element name="Content">
        <xsl:element name="Metadata">
          <xsl:element name="NewsItemID">
            <xsl:text>0</xsl:text>
          </xsl:element>
          <xsl:element name="ContentItemID">
            <xsl:text>0</xsl:text>
          </xsl:element>
          <xsl:element name="OriginalSourceID">
            <xsl:value-of select="$m_ManagementId" />
          </xsl:element>
          <xsl:element name="ContainerID" />
          <xsl:element name="Abstract">
            <xsl:value-of select="atom:title" />
            <xsl:if test="apcm:ContentMetadata/apcm:HeadLine">
              <xsl:value-of select="concat('. ', apcm:ContentMetadata/apcm:HeadLine)" />
            </xsl:if>
          </xsl:element>
          <xsl:element name="ANPACategories" />
          <xsl:element name="AssetComments" />
          <xsl:element name="Contributors">
            <xsl:apply-templates select="atom:contributor" />
          </xsl:element>
          <xsl:element name="Creator">
            <!-- Create comma separated byline list. -->
            <xsl:variable name="m_ByLine">
              <xsl:for-each select="apcm:ContentMetadata/apcm:ByLine">
                <xsl:variable name="m_Person">
                  <xsl:choose>
                    <xsl:when test="starts-with(normalize-space(.), 'By')">
                      <xsl:value-of select="normalize-space(substring-after(normalize-space(.), 'By'))" />
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="normalize-space(.)" />
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:variable>
                <xsl:if test="string-length($m_Person) != 0 and not(starts-with($m_Person, 'The Associated Press'))">
                  <xsl:value-of select="concat(',', $m_Person)" />
                </xsl:if>
              </xsl:for-each>
            </xsl:variable>
            <xsl:if test="starts-with($m_ByLine, ',')">
              <!-- output the byline, but remove any instances of {Dash}{Dash}PAR in the byline -->
              <xsl:call-template name="string-replace-all">
                <xsl:with-param name="text"
                  select="cp:STR_ProperCaseName(normalize-space(substring-after($m_ByLine, ',')))" />
                <xsl:with-param name="find">--Par</xsl:with-param>
                <xsl:with-param name="replace"></xsl:with-param>
              </xsl:call-template>
              <!--<xsl:value-of select="cp:STR_ProperCaseName(normalize-space(substring-after($m_ByLine, ',')))" />-->
            </xsl:if>
          </xsl:element>
          <xsl:element name="CreatorStatus" />
          <xsl:element name="DeleteMe">
            <xsl:text>false</xsl:text>
          </xsl:element>
          <xsl:element name="FileName">
            <xsl:value-of select="concat($m_EntryId, '.xml')" />
          </xsl:element>
          <xsl:element name="FilePath" />
          <xsl:element name="NewsItemName">
            <xsl:variable name="m_CategoryValue"
              select="normalize-space(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code']/@Value)" />
            <xsl:variable name="m_Lang">
              <xsl:choose>
                <xsl:when
                  test="apcm:ContentMetadata/apcm:Property[@Name='EntitlementMatch' and @Value='French News Service']">
                  <xsl:text>FR</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>EN</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:variable>
            <xsl:choose>
              <xsl:when test="string-length($m_CategoryValue) != 0">
                <xsl:value-of select="concat('auto:', $m_Lang, ':', $m_CategoryValue, ':00000')" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>auto:mht:mht:00000</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
            <!--<xsl:value-of select="apcm:ContentMetadata/apcm:TransmissionReference" />-->
          </xsl:element>
          <xsl:element name="FileSize" />
          <xsl:element name="FullText">
            <xsl:apply-templates select="atom:content/nitf/body/body.content/block" />
            <xsl:apply-templates select="atom:content/atom:nitf/atom:body/atom:body.content/atom:block" />
          </xsl:element>
          <xsl:element name="KeywordsExternal">
            <!-- Create comma separated keywords list. -->
            <xsl:variable name="m_Keywords">
              <xsl:for-each select="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject']">
                <xsl:value-of select="concat(',', @Value)" />
              </xsl:for-each>
            </xsl:variable>
            <xsl:if test="starts-with($m_Keywords, ',')">
              <xsl:value-of select="normalize-space(substring-after($m_Keywords, ','))" />
            </xsl:if>
          </xsl:element>
          <xsl:element name="ReleaseDate">
            <xsl:choose>
              <xsl:when test="apnm:NewsManagement/apnm:PublishingStatus = 'Embargoed'">
                <xsl:value-of select="concat(apnm:NewsManagement/apnm:PublishingStatus/@statusChangeOn, 'Z')" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>0001-01-01T00:00:00Z</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>

          <xsl:element name="Sources">
            <!--<xsl:apply-templates select="atom:content/nitf/body/body.head/distributor" />
					<xsl:apply-templates select="atom:content/atom:nitf/atom:body/atom:body.head/atom:distributor" />-->
            <!-- The source is always The Associated Press -->
            <xsl:element name="Source">
              <xsl:text>The Associated Press</xsl:text>
            </xsl:element>
            <xsl:if test="atom:contributor">
              <xsl:element name="Source">
                <xsl:text>AP Member</xsl:text>
              </xsl:element>
            </xsl:if>
          </xsl:element>
          <xsl:element name="ThirdParties" />
          <xsl:element name="WordCount">
            <xsl:text>0</xsl:text>
          </xsl:element>
          <xsl:element name="ANPAGraphicType">
            <xsl:choose>
              <xsl:when test="$m_GraphicCount > 1">
                <xsl:text>Many</xsl:text>
              </xsl:when>
              <xsl:when test="$m_GraphicCount = 1">
                <xsl:text>One</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>None</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="ANPAPhotoType">
            <xsl:choose>
              <xsl:when test="$m_PhotoCount > 1">
                <xsl:text>Many</xsl:text>
              </xsl:when>
              <xsl:when test="$m_PhotoCount = 1">
                <xsl:text>One</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>None</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="ANPAVideoType">
            <xsl:choose>
              <xsl:when test="$m_VideoCount > 1">
                <xsl:text>Many</xsl:text>
              </xsl:when>
              <xsl:when test="$m_VideoCount = 1">
                <xsl:text>One</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>None</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="ANPAAudioType">
            <xsl:choose>
              <xsl:when test="$m_AudioCount > 1">
                <xsl:text>Many</xsl:text>
              </xsl:when>
              <xsl:when test="$m_AudioCount = 1">
                <xsl:text>One</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>None</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <!--<xsl:element name="ANPAPhotoNumbers">
					<xsl:value-of select="$m_PhotoCount" />
				</xsl:element>-->
          <xsl:element name="ANPASelectorCodes">
            <xsl:apply-templates select="apcm:ContentMetadata/apcm:Selector" />
          </xsl:element>
          <xsl:element name="ANPALocalsOuts" />
          <xsl:element name="City">
            <xsl:value-of select="apcm:ContentMetadata/apcm:DateLineLocation/@City" />
          </xsl:element>
          <xsl:element name="CopyrightNotice">
            <xsl:value-of select="atom:rights" />
          </xsl:element>
          <xsl:element name="EditorsNote">
            <xsl:choose>
              <xsl:when test="string-length($m_APNewsNow) != 0 and
						                string-length($m_MovingOn) != 0">
                <xsl:value-of select="concat($m_APNewsNow, ' ', $m_MovingOn)" />
              </xsl:when>
              <xsl:when test="string-length($m_APNewsNow) != 0">
                <xsl:value-of select="$m_APNewsNow" />
              </xsl:when>
              <xsl:when test="string-length($m_MovingOn) != 0">
                <xsl:value-of select="$m_MovingOn" />
              </xsl:when>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="GeoTag" />

          <!-- If there is no extended headline, use the short headline -->
          <xsl:element name="HeadlineExtended">
            <xsl:choose>
              <xsl:when test="string-length($m_HeadlineExtended)">
                <xsl:value-of select="$m_HeadlineShort" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="$m_HeadlineShort" />
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>

          <!-- If there is no short headline, use the extended headline -->
          <xsl:element name="HeadlineShort">
            <xsl:choose>
              <xsl:when test="string-length($m_HeadlineShort)">
                <xsl:value-of select="$m_HeadlineShort" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="$m_HeadlineShort" />
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>

          <xsl:element name="Importance" />
          <xsl:element name="IndexCodes">
            <!--<xsl:apply-templates select="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject']" />-->
            <xsl:apply-templates
              select="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code']" />
            <xsl:call-template name="APEntitlementMatchCodes" />
          </xsl:element>
          <xsl:element name="ISOCountryCodes" />
          <xsl:element name="Language">
            <xsl:choose>
              <xsl:when
                test="apcm:ContentMetadata/apcm:Property[@Name='EntitlementMatch' and @Value='French News Service']">
                <xsl:attribute name="Label">
                  <xsl:text>French</xsl:text>
                </xsl:attribute>
                <xsl:text>FR</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:attribute name="Label">
                  <xsl:text>English</xsl:text>
                </xsl:attribute>
                <xsl:text>EN</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="PlaceLine">
            <xsl:value-of select="apcm:ContentMetadata/apcm:DateLine" />
          </xsl:element>
          <xsl:element name="Priority">
            <xsl:value-of select="apcm:ContentMetadata/apcm:Priority/@Legacy" />
          </xsl:element>
          <xsl:element name="Provider">
            <xsl:text>The Associated Press</xsl:text>
          </xsl:element>
          <xsl:element name="Province">
            <xsl:value-of select="apcm:ContentMetadata/apcm:DateLineLocation/@CountryAreaName" />
          </xsl:element>
          <xsl:element name="Ranking">
            <xsl:call-template name="RankingProcess">
              <xsl:with-param name="m_SlugLine">
                <xsl:value-of select="$m_SlugLine" />
              </xsl:with-param>
            </xsl:call-template>
          </xsl:element>
          <xsl:element name="Country">
            <xsl:value-of select="apcm:ContentMetadata/apcm:DateLineLocation/@CountryName" />
          </xsl:element>
          <xsl:element name="Services" />
          <xsl:element name="SlugLine">
            <xsl:value-of select="$m_SlugLine" />
          </xsl:element>
          <xsl:element name="Stocks">
            <!-- Create comma separated stocks list. -->
            <xsl:variable name="m_Stocks">
              <xsl:for-each select="apcm:ContentMetadata/apcm:EntityClassification[@Authority='AP Company']">
                <xsl:variable name="m_PrimaryTicker">
                  <xsl:call-template name="FNC_ToUpperCase">
                    <xsl:with-param name="P_String" select="apcm:Property[@Name='PrimaryTicker']/@Value" />
                  </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="m_Exchange" select="apcm:Property[@Name='Exchange']/@Value" />
                <xsl:if test="string-length(normalize-space($m_PrimaryTicker)) != 0">
                  <xsl:choose>
                    <xsl:when test="string-length(normalize-space($m_Exchange)) != 0">
                      <xsl:value-of select="concat(',', $m_Exchange, ':', $m_PrimaryTicker)" />
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="concat(',', $m_PrimaryTicker)" />
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:if>
              </xsl:for-each>
            </xsl:variable>
            <xsl:if test="starts-with($m_Stocks, ',')">
              <xsl:value-of select="normalize-space(substring-after($m_Stocks, ','))" />
            </xsl:if>
          </xsl:element>
          <xsl:element name="SubTitle" />
          <xsl:element name="TopStory">
            <xsl:choose>
              <xsl:when
                test="apcm:ContentMetadata/apcm:Property[@Name='Top Headline Parent' or @Name='Top Headline Children']">
                <xsl:text>true</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>false</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="Type" />
          <xsl:element name="Update">
            <xsl:value-of select="cp:REGEX_Replace(cp:REGEX_Replace($m_Eds, '\s*Moving on.*\.', ''), 'NDLR\:', '')" />
          </xsl:element>
          <xsl:element name="VersionType">
            <xsl:choose>
              <xsl:when test="string-length(cp:REGEX_Match(atom:title, '(?i)APNewsAlert')) != 0">
                <xsl:text>NewsAlert</xsl:text>
              </xsl:when>
              <xsl:when
                test="string-length(cp:REGEX_Match(apcm:ContentMetadata/apcm:HeadLine, '(?i)Correction:')) != 0">
                <xsl:text>Corrective</xsl:text>
              </xsl:when>
              <xsl:when test="apnm:NewsManagement/apnm:PublishingStatus = 'Canceled'">
                <xsl:text>Kill</xsl:text>
              </xsl:when>
              <xsl:when test="apnm:NewsManagement/apnm:PublishingStatus = 'Withheld'">
                <xsl:text>Withhold</xsl:text>
              </xsl:when>
              <xsl:when test="apnm:NewsManagement/apnm:PublishingStatus = 'Embargoed'">
                <xsl:text>Embargoed</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:if
                  test="apcm:ContentMetadata/apcm:ItemContentType and string-length(normalize-space(apcm:ContentMetadata/apcm:ItemContentType)) !=0">
                  <xsl:value-of select="apcm:ContentMetadata/apcm:ItemContentType" />
                </xsl:if>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="PendingApproval">
            <xsl:text>false</xsl:text>
          </xsl:element>
          <xsl:element name="WriteThruType">
            <xsl:choose>
              <xsl:when
                test="apnm:NewsManagement/apnm:PublishingStatus = 'Canceled' or apnm:NewsManagement/apnm:PublishingStatus = 'Withheld'">
                <xsl:text>Writethru Correction</xsl:text>
              </xsl:when>
              <xsl:when test="number(apnm:NewsManagement/apnm:ManagementSequenceNumber) > 0">
                <xsl:text>Writethru</xsl:text>
              </xsl:when>
            </xsl:choose>
          </xsl:element>
          <xsl:element name="WriteThruNumber">
            <xsl:value-of select="apnm:NewsManagement/apnm:ManagementSequenceNumber" />
          </xsl:element>
          <xsl:element name="WriteThruValue">
            <xsl:value-of select="apnm:NewsManagement/apnm:ManagementSequenceNumber" />
          </xsl:element>
        </xsl:element>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code']">

    <!-- Set the language, if the entitlement match for French News Service is found, it is french. 
    Otherwise, the language is English. Use FR and EN respectively. -->
    <xsl:variable name="m_Language">
      <xsl:choose>
        <!-- Check if this is a french file -->
        <xsl:when
          test="count(apcm:ContentMetadata/apcm:Property[@Name='EntitlementMatch' and @Value='French News Service']) > 0">
          <xsl:text>FR</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>EN</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="m_SlugLine"
      select="cp:REGEX_Replace(translate(/atom:entry/atom:title, ' ', '-'), '-{2}', '-')" />

    <xsl:element name="IndexCode">
      <xsl:choose>
        <!-- French File -->
        <xsl:when test="$m_Language = 'FR'">
          <xsl:choose>
            <xsl:when test="@Id = 'a'">


              <xsl:text>Culture</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'i' or @Id = 'n'">
              <xsl:text>International</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'g'">
              <xsl:text>
                <![CDATA[Nouvelles Générales]]>
              </xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 's'">
              <xsl:text>Sports</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>Spare News</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>

        <!-- English File -->
        <xsl:otherwise>
          <xsl:choose>

            <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, 
              '(?x)-MED-')) != 0">
              <xsl:text>Lifestyle</xsl:text>
            </xsl:when>

            <!--
              We check for agate indciators by checking the Legacy Type set format which will be set to 't' for tabular files,
              as well as in the EntitlementMatches which will have an id of 31385 for 'S Level Sports - Agate Only'
            -->
            <xsl:when
              test="string-length(cp:REGEX_Match(../apcm:if(, '(?i)(t)')) != 0 or                        
                                  count(../apcm:Property[@Name='EntitlementMatch' and @Id='urn:publicid:ap.org:product:31385']) != 0">
              <xsl:text>Agate</xsl:text>
            </xsl:when>

            <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, 
              '(?ix)(ARC	(?# Match for Archery)
                |ATH	(?# Match for Athletics)
                |BAD	(?# Match for Badminton)
                |BBA	(?# Match for Baseball American League)
                |BBC	(?# Match for Baseball U.S. College)
                |BBH	(?# Match for Baseball High School)
                |BBI	(?# Match for Baseball International)
                |BBM	(?# Match for Baseball Minor Leagues)
                |BBN	(?# Match for Baseball National League)
                |BBO	(?# Match for Baseball Other)
                |BBW	(?# Match for Baseball Women)
                |BBY	(?# Match for Baseball Youth)
                |BIA	  (?# Match for Biathalon)
                |BKC	(?# Match for Basketball U.S. College)
                |BKH	(?# Match for Basketball High School)
                |BKL	(?# Match for Basketball Womens Pro)
                |BKN	(?# Match for Basketball NBA)
                |BKO	(?# Match for Basketball Other)
                |BKW	(?# Match for Basketball Womens College)
                |BOB	(?# Match for Bobsled)
                |BOX	(?# Match for Boxing)
                |CAN	(?# Match for Canoeing)
                |CAR	(?# Match for Auto Racing)
                |COM	(?# Match for Commonwealth Games)
                |CRI	(?# Match for Cricket)
                |CUR	(?# Match for Curling)
                |CYC	(?# Match for Cycling)
                |DIV	(?# Match for Diving)
                |EQU	(?# Match for Equestrian)
                |FBC	(?# Match for Football U.S. College)
                |FBH	(?# Match for Football High School)
                |FBN	(?# Match for Football NFL)
                |FBO	(?# Match for Football Other)
                |FEN	(?# Match for Fencing)
                |FHK	(?# Match for Field Hockey)
                |FIG	(?# Match for Figure Skating)
                |FRE	(?# Match for Freestyle skiing)
                |GLF	(?# Match for Golf)
                |GYM	(?# Match for Gymnastics)
                |HKC	(?# Match for Hockey U.S. College)
                |HKN	(?# Match for Hockey NHL)
                |HKO	(?# Match for Hockey Other)
                |HKW	(?# Match for Hockey Women)
                |HNB	(?# Match for Handball)
                |JUD	(?# Match for Judo)
                |JUM	(?# Match for Ski jumping)
                |LUG	(?# Match for Luge)
                |MMA	(?# Match for Mixed martial arts)
                |MOT	(?# Match for Motorcycling)
                |NOR	(?# Match for Nordic Combined)
                |OLY	(?# Match for Olympics)
                |PEN	(?# Match for Modern Pentathlon)
                |RAC	(?# Match for Horseracing)
                |RGL	(?# Match for RugbyLeague)
                |RGU	(?# Match for RugbyUnion)
                |ROW	(?# Match for Rowing)
                |SAI	(?# Match for Sailing)
                |SBD	(?# Match for Snowboarding)
                |SHO	(?# Match for Short track)
                |SKE	(?# Match for Skeleton)
                |SKI	(?# Match for Skiing - Alpine)
                |SOC	(?# Match for Soccer)
                |SOF	(?# Match for Softball)
                |SPD	(?# Match for Speedskating long track)
                |SQA	(?# Match for Squash)
                |SUM	(?# Match for Sumo Wrestling)
                |SWM	(?# Match for Swimming)
                |TAE	(?# Match for Taekwondo)
                |TEN	(?# Match for Tennis)
                |TRI	(?# Match for Triathlon)
                |TTN	(?# Match for Table tennis)
                |VOL	(?# Match for Volleyball)
                |WEI	(?# Match for Weightlifting)
                |WPO	(?# Match for WaterPolo)
                |WRE	(?# Match for Wrestling)
                |XXC	(?# Match for Cross-country skiing)
                )
                .*
                (Box		(?# Match for Box)
                |Calendar	(?# Match for Calendar)
                |Comparison	(?# Match for Comparison)
                |Date		(?# Match for Date)
                |Digest		(?# Match for Digest)
                |Fared		(?# Match for Fared)
                |Glance		(?# Match for Glance)
                |Leaders	(?# Match for Leaders)
                |Poll		(?# Match for Poll)
                |Results?	(?# Match for Results)
                |Linescores	(?# Match for Linescores)
                |Schedule	(?# Match for Schedule)
                |Scores?	(?# Match for Score)
                |Scorers	(?# Match for Scorers)
                |Scoreboard	(?# Match for Scoreboard)
                |Standings	(?# Match for Standings)
                |Stax		(?# Match for Stax)
				|Streaks?    (?# Match for baseball streak files
                |Sums?		(?# Match for Sum)
                |Summaries	(?# Match for Summaries)
                |Glantz-Culver-Line	(?# Match for Glantz-Culver-Line)
                )'
              )) != 0">
              <xsl:text>Agate</xsl:text>
            </xsl:when>

            <xsl:when test="@Id = 'a' or
			                @Id = 'b' or
			                @Id = 'i' or
			                @Id = 'k' or
			                @Id = 'n' or
			                @Id = 'w'">
              <xsl:text>International</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'd' or @Id = 'l'">
              <xsl:text>Lifestyle</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'e' or @Id = 'c'">
              <xsl:text>Entertainment</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'f'">
              <xsl:text>Business</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'p'">
              <xsl:text>Politics</xsl:text>
            </xsl:when>
            <xsl:when test="@Id = 'q' or	@Id = 's' or @Id = 'z'">
              <xsl:text>Sports</xsl:text>
              <!-- Adding Olympics to spare sports              
              <xsl:choose>

                <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, '.*OLY-')) != 0">
                  <xsl:text>Spare Sports</xsl:text>    
                </xsl:when>
				
                <xsl:otherwise>
                  <xsl:text>Sports</xsl:text>
                </xsl:otherwise>                 
              </xsl:choose>				
              -->
            </xsl:when>

            <xsl:when test="@Id = 't'">
              <xsl:text>Travel</xsl:text>
            </xsl:when>

            <xsl:when test="@Id = 'v'">
              <xsl:text>Advisories</xsl:text>
            </xsl:when>

            <xsl:when
              test="string-length(cp:REGEX_Match($m_SlugLine, 'Washington-Digest|AP-Newsfeatures-Digest')) != 0">
              <xsl:text>Prairies/BC</xsl:text>
            </xsl:when>

            <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, 'AP-Newsfeatures-Digest')) != 0">
              <xsl:text>International</xsl:text>
            </xsl:when>

            <xsl:otherwise>
              <xsl:text>Spare News</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>

    </xsl:element>
  </xsl:template>

  <xsl:template match="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject']">
    <!-- Business c8e409f8858510048872ff2260dd383e -->
    <!-- Entertainment 5b4319707dd310048b23df092526b43e -->
    <!-- Environment and nature 8783d248894710048286ba0a2b2ca13e -->
    <!-- General news f25af2d07e4e100484f5df092526b43e -->
    <!-- Government and politics 86aad5207dac100488ecba7fa5283c3e -->
    <!-- Health cc7a76087e4e10048482df092526b43e -->
    <!-- Lifestyle 3e37e4b87df7100483d5df092526b43e -->
    <!-- Oddities 44811870882f10048079ae2ac3a6923e -->
    <!-- Science 4bf76cb87df7100483dbdf092526b43e -->
    <!-- Social affairs 75a42fd87df7100483eedf092526b43e -->
    <!-- Sports 54df6c687df7100483dedf092526b43e -->
    <!-- Technology 455ef2b87df7100483d8df092526b43e -->
    <xsl:if test="@Id = 'c8e409f8858510048872ff2260dd383e' or
	              @Id = '5b4319707dd310048b23df092526b43e' or
				  @Id = '8783d248894710048286ba0a2b2ca13e' or
				  @Id = 'f25af2d07e4e100484f5df092526b43e' or
				  @Id = '86aad5207dac100488ecba7fa5283c3e' or
				  @Id = 'cc7a76087e4e10048482df092526b43e' or
				  @Id = '3e37e4b87df7100483d5df092526b43e' or
				  @Id = '44811870882f10048079ae2ac3a6923e' or
				  @Id = '4bf76cb87df7100483dbdf092526b43e' or
				  @Id = '75a42fd87df7100483eedf092526b43e' or
				  @Id = '54df6c687df7100483dedf092526b43e' or
				  @Id = '455ef2b87df7100483d8df092526b43e'">
      <xsl:element name="IndexCode">
        <xsl:value-of select="normalize-space(@Value)" />
      </xsl:element>
    </xsl:if>
  </xsl:template>

  <!-- Contributor -->
  <xsl:template match="atom:contributor">
    <xsl:if test="string-length(normalize-space(atom:name)) != 0">
      <xsl:element name="Contributor">
        <xsl:value-of select="atom:name" />
      </xsl:element>
    </xsl:if>
  </xsl:template>

  <!-- Source -->
  <xsl:template match="nitf/body/body.head/distributor|atom:nitf/atom:body/atom:body.head/atom:distributor">
    <xsl:if test="string-length(normalize-space(.)) != 0">
      <xsl:element name="Source">
        <xsl:value-of select="normalize-space(.)" />
      </xsl:element>
    </xsl:if>
  </xsl:template>

  <!-- ANPASelectorCodes -->
  <xsl:template match="apcm:ContentMetadata/apcm:Selector">
    <xsl:element name="ANPASelectorCodes">
      <xsl:value-of select="." />
    </xsl:element>
  </xsl:template>

  <!-- FullText -->
  <xsl:template match="block|atom:block">
    <xsl:apply-templates select="node()" />
  </xsl:template>

  <!-- Node -->
  <xsl:template match="node()">
    <xsl:variable name="m_NodeName">
      <xsl:call-template name="FNC_ToLowerCase">
        <xsl:with-param name="P_String" select="local-name()" />
      </xsl:call-template>
    </xsl:variable>

    <!-- Convert the following non <p> tags into <p> -->
    <xsl:choose>
      <xsl:when test="$m_NodeName = 'hl2'">
        <xsl:element name="p">
          <xsl:apply-templates select="@*" />
          <xsl:apply-templates select="node()" />
        </xsl:element>
      </xsl:when>
      <xsl:when test="$m_NodeName = 'note'">
        <xsl:element name="p">
          <xsl:apply-templates select="@*" />
          <xsl:apply-templates select="node()" />
        </xsl:element>
      </xsl:when>
      <xsl:when test="$m_NodeName = 'pre'">
        <xsl:element name="p">
          <xsl:apply-templates select="@*" />
          <xsl:apply-templates select="node()" />
        </xsl:element>
      </xsl:when>
      <xsl:otherwise>
        <xsl:element name="{$m_NodeName}">
          <xsl:apply-templates select="@*" />
          <xsl:apply-templates select="node()" />
        </xsl:element>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- Text -->
  <xsl:template match="text()">
    <xsl:if test="string-length(normalize-space(.)) != 0">
      <xsl:choose>
        <xsl:when
          test="parent::p and /atom:entry/apcm:ContentMetadata/apcm:DateLine and contains(self::text(), /atom:entry/apcm:ContentMetadata/apcm:DateLine) and string-length(cp:REGEX_Match(self::text(), '^.+?\s+\(AP\)\s+[-–—―]\s*')) != 0">
          <xsl:value-of select="cp:REGEX_Replace(self::text(), '^.+?\s+\(AP\)\s+[-–—―]\s*', '')" />
        </xsl:when>
        <xsl:when
          test="parent::atom:p and /atom:entry/apcm:ContentMetadata/apcm:DateLine and contains(self::text(), /atom:entry/apcm:ContentMetadata/apcm:DateLine) and string-length(cp:REGEX_Match(self::text(), '^.+?\s+\(AP\)\s+[-–—―]\s*')) != 0">
          <xsl:value-of select="cp:REGEX_Replace(self::text(), '^.+?\s+\(AP\)\s+[-–—―]\s*', '')" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="self::text()" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

  <!-- Attributes we should ignore. -->
  <xsl:template match="@class|@CLASS|@Class" />
  <xsl:template match="@id|@ID|@Id" />
  <!--<xsl:template match="@target|@TARGET|@Target" />-->

  <!-- Attributes -->
  <xsl:template match="@*">
    <xsl:variable name="m_NodeName">
      <xsl:call-template name="FNC_ToLowerCase">
        <xsl:with-param name="P_String" select="local-name()" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:attribute name="{$m_NodeName}">
      <xsl:value-of select="normalize-space(.)" />
    </xsl:attribute>
  </xsl:template>

  <!-- DWC Additions: Headline Processing templates -->
  <!--
	Template to process the headline nodes from AP content.
	It strips any mdash or under scores and replaces them with a 
	space dash space string instead. 
	-->
  <xsl:template name="ProcessHeadline">
    <xsl:param name="Value"></xsl:param>

    <!-- Mdash variable, used to find during replace attempts -->
    <xsl:variable name="MDash">—</xsl:variable>
    <!-- The replace value, a space/dash/space combo -->
    <xsl:variable name="SpaceDashSpace">
      <xsl:text> - </xsl:text>
    </xsl:variable>

    <!-- Remove APNewsBreak-->
    <xsl:variable name="cleaned-value">
      <xsl:call-template name="string-replace-all">
        <xsl:with-param name="text" select="$Value" />
        <xsl:with-param name="find" select="'APNewsBreak: '" />
        <xsl:with-param name="replace" select="''" />
      </xsl:call-template>
    </xsl:variable>

    <!-- Create a temp variable and process the headline for the mdash -->
    <xsl:variable name="no-mdash">
      <xsl:call-template name="string-replace-all">
        <xsl:with-param name="text" select="$cleaned-value" />
        <xsl:with-param name="find" select="$MDash" />
        <xsl:with-param name="replace" select="$SpaceDashSpace" />
      </xsl:call-template>
    </xsl:variable>

    <!-- Call the template again to process underscores, outputting the result -->
    <xsl:call-template name="string-replace-all">
      <xsl:with-param name="text" select="$no-mdash" />
      <xsl:with-param name="find">_</xsl:with-param>
      <xsl:with-param name="replace" select="$SpaceDashSpace" />
    </xsl:call-template>
  </xsl:template>

  <!-- 
    Template to append certain index code values based on the type of feed. This is based
    on the value in the Property node with name attribute of EntitlementMatch.  There are several
    of these nodes, so we loop through each and check them all.
    -->
  <xsl:template name="APEntitlementMatchCodes">
    <xsl:for-each select="apcm:ContentMetadata/apcm:Property[@Name='EntitlementMatch']">
      <xsl:choose>
        <xsl:when test="@Value = 'AP Online Top U.S. News Short Headlines'">
          <xsl:element name="IndexCode">
            <xsl:text>International</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'AP Online Top Business Short Headlines'">
          <xsl:element name="IndexCode">
            <xsl:text>Business</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'AP Online Top Entertainment Short Headlines'">
          <xsl:element name="IndexCode">
            <xsl:text>Entertainment</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'Top Stories-code 9020 AP Online Top Headlines Health'">
          <xsl:element name="IndexCode">
            <xsl:text>Health</xsl:text>
          </xsl:element>
          <xsl:element name="IndexCode">
            <xsl:text>Lifestyle</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'AP Online Top International Short Headlines'">
          <xsl:element name="IndexCode">
            <xsl:text>International</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'AP Online Top Strange Headlines'">
          <xsl:element name="IndexCode">
            <xsl:text>International</xsl:text>
          </xsl:element>
          <xsl:element name="IndexCode">
            <xsl:text>Human Interest</xsl:text>
          </xsl:element>
        </xsl:when>

        <xsl:when test="@Value = 'AP Online Headlines - Science'">
          <xsl:element name="IndexCode">
            <xsl:text>Lifestyle</xsl:text>
          </xsl:element>
          <xsl:element name="IndexCode">
            <xsl:text>Science</xsl:text>
          </xsl:element>
        </xsl:when>

      </xsl:choose>
    </xsl:for-each>

  </xsl:template>

  <!-- 
      Ranking Template, used to attach custom ranking to AP stories as decided by AP. There is a word document
      that explains these rules in a table format.  It should be used as a reference guide.
   -->
  <xsl:template name="RankingProcess">
    <xsl:param name="m_SlugLine" />

    <xsl:variable name="m_ContentType">
      <xsl:choose>
        <xsl:when test="apcm:ContentMetadata/apcm:ItemContentType != ''">
          <xsl:value-of select="apcm:ContentMetadata/apcm:ItemContentType" />
        </xsl:when>
        <xsl:when
          test="apcm:ContentMetadata/apcm:Property[@Name='Top Headline Parent' or @Name='Top Headline Children']">
          <xsl:text>TopStory</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>Unknown</xsl:text>
        </xsl:otherwise>
      </xsl:choose>

    </xsl:variable>
    <xsl:variable name="m_Priority" select="apcm:ContentMetadata/apcm:Priority/@Legacy" />
    <!-- Set the language, if the entitlement match for French News Service is found, it is french. 
    Otherwise, the language is English. Use FR and EN respectively. -->
    <xsl:variable name="m_Language">
      <xsl:choose>
        <!-- Check if this is a french file -->
        <xsl:when
          test="count(apcm:ContentMetadata/apcm:Property[@Name='EntitlementMatch' and @Value='French News Service']) > 0">
          <xsl:text>FR</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>EN</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <!-- Find the ID of the Subject Code (index code) - Used for an Agate condition below -->
    <xsl:variable name="Id"
      select="apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code']/@Id" />

    <xsl:choose>
      <!-- Check if this is a french file -->
      <xsl:when test="$m_Language = 'FR'">
        <!-- The french file ranking logic, contains an inner choose statement -->
        <xsl:choose>
          <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, '(?i)^(insolite)')) != 0">
            <xsl:text>News - Buzz</xsl:text>
          </xsl:when>
          <xsl:when test="string-length(cp:REGEX_Match($m_Priority, '(?i)(f|b)')) != 0">
            <xsl:text>News - Urgent</xsl:text>
          </xsl:when>
          <xsl:when test="string-length(cp:REGEX_Match($m_Priority, '(?i)u')) != 0">
            <xsl:text>News - Need to know</xsl:text>
          </xsl:when>
          <xsl:when test="string-length(cp:REGEX_Match($m_Priority, '(?i)r')) != 0">
            <xsl:text>News - Good to know</xsl:text>
          </xsl:when>
          <xsl:when test="string-length(cp:REGEX_Match($m_Priority, '(?i)d')) != 0">
            <xsl:text>News - Optional</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>News - Optional</xsl:text>
          </xsl:otherwise>
        </xsl:choose>

      </xsl:when>

      <!--Make sure file type is    : apv	
			Subject Classification    : Sports
			Slug                      : CYC|FIG|SKI|TEN
			Then the file Ranking     : News - Good to know-->
      <xsl:when test="contains(apcm:ContentMetadata/apcm:Property[@Name = 'EntitlementMatch' and @Id = 'urn:publicid:ap.org:product:32607']/@Value,'European News Service')  and						
            count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code' and @Id='s']) > 0 and
						(string-length(cp:REGEX_Match($m_SlugLine, '(?i)(CYC|FIG|OLY|SKI|TEN)-')) != 0)">
        <xsl:text>News - Good to know</xsl:text>
      </xsl:when>

      <!--Make sure file type is    : aps
          Subject Classification    : Sports
          Slug                      : CAR|BBA|BBN|BKN|FBN|GLF|HKN|LAC|OLY|RAC|MMA
          Then the file Ranking     : News - Good to know-->
      <xsl:when test="contains(apcm:ContentMetadata/apcm:Property[@Name = 'EntitlementMatch' and @Id = 'urn:publicid:ap.org:product:30599']/@Value,'AP Sports News (S Wire only)')  and						
              count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code' and @Id='s']) > 0 and
						  (string-length(cp:REGEX_Match($m_SlugLine, '(?i)(CAR|BBA|BBN|BKN|FBN|GLF|HKN|LAC|OLY|RAC|MMA)-')) != 0)">
        <xsl:text>News - Good to know</xsl:text>
      </xsl:when>

      <!--Make sure file type is    : apv				
			Slug                      : ARC|ATH|BAD|BIA|BOB|CAN|CRI|XXC|CUR|DIV|EQU|FEN|FHK|FRE|GYM|HNB|JUD|LUG|PEN|MOT|NOR|ROW|RGL|RGU|SAI|SHO|SKE|JUM|SBD|SOC|SOF|SPD|SQA|SUM|SWM|TTN|TAE|TRI|VOL|WPO|WEI|WRE
			Then the file Ranking     : News - Good to know-->
      <xsl:when
        test="contains(apcm:ContentMetadata/apcm:Property[@Name = 'EntitlementMatch' and @Id = 'urn:publicid:ap.org:product:32607']/@Value,'European News Service')  and						
            count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code' and @Id='s']) > 0 and
						(string-length(cp:REGEX_Match($m_SlugLine, '(?i)(ARC|ATH|BAD|BIA|BOB|CAN|CRI|XXC|CUR|DIV|EQU|FEN|FHK|FRE|GYM|HNB|JUD|LUG|PEN|MOT|NOR|ROW|RGL|RGU|SAI|SHO|SKE|JUM|SBD|SOC|SOF|SPD|SQA|SUM|SWM|TTN|TAE|TRI|VOL|WPO|WEI|WRE)-')) != 0)">
        <xsl:text>News - Optional</xsl:text>
      </xsl:when>

      <!--Make sure file type is    : aps
			Subject Classification    : Sports
			Slug                      : BBC|BBH|BBI|BBM|BBW|BBY|BKC|BKH|BKO|BKW|BKL|BOX|FBC|FBH|FBO|HKC|HKO|HKW
			Then the file Ranking     : News - Good to know-->
      <xsl:when
        test="contains(apcm:ContentMetadata/apcm:Property[@Name = 'EntitlementMatch' and @Id = 'urn:publicid:ap.org:product:30599']/@Value,'AP Sports News (S Wire only)')  and						
            count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Category Code' and @Id='s']) > 0 and
						(string-length(cp:REGEX_Match($m_SlugLine, '(?i)(BBC|BBH|BBI|BBM|BBW|BBY|BKC|BKH|BKO|BKW|BKL|BOX|FBC|FBH|FBO|HKC|HKO|HKW)-')) != 0)">
        <xsl:text>News - Optional</xsl:text>
      </xsl:when>

      <!-- If this slug contains the phrase "today in history" -->
      <xsl:when test="string-length(cp:REGEX_Match($m_SlugLine, '(?i)today-in-history')) != 0">
        <xsl:text>Routine</xsl:text>
      </xsl:when>

      <!--1. File contenttype          : If "Spot Development" AND	
          2. Slug Contains             : Word "ODD" or "PEOPLE" Go to 4.
          3. File contenttype          : AP Impact	
          4. Priority Code             : Anything (so dont need to check)
          5. Subject Classification    : Dont Check
          6. Then the file Ranking     : News - Buzz-->
      <xsl:when test="(
                        string-length(cp:REGEX_Match($m_SlugLine, '(?i)(odd|people)')) != 0 and
                        string-length(cp:REGEX_Match($m_ContentType, '(?i)(spot)')) != 0
                      ) or
						         string-length(cp:REGEX_Match($m_ContentType, '(?i)ap\s+impact')) != 0">
        <xsl:text>News - Buzz</xsl:text>
      </xsl:when>

      <!--Flie contenttype          : Spot Development
          Priority Code             : R
          Subject Classification    : Entertainment
          Then the file Ranking     : News - Buzz-->
      <xsl:when
        test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(spot)')) != 0 and
						          string-length(cp:REGEX_Match($m_Priority, '(?i)r')) != 0 and
                      count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject' and @Id='5b4319707dd310048b23df092526b43e']) > 0">
        <xsl:text>News - Buzz</xsl:text>
      </xsl:when>

      <!--File contenttype          : Game story	
          Priority Code             : anything (so dont need to check)
          Subject Classification    : Sports
          Then the file Ranking     : News - Good to know-->
      <xsl:when
        test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(game)')) != 0 and
                      count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject' and @Id='54df6c687df7100483dedf092526b43e']) > 0">
        <xsl:text>News - Good to know</xsl:text>
      </xsl:when>

      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)obituary')) != 0 and
						    string-length(cp:REGEX_Match($m_Priority, '(?i)u')) != 0">
        <xsl:text>News - Urgent</xsl:text>
      </xsl:when>
      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(spot|game|topstory|headlinepackage)')) != 0 and
						    string-length(cp:REGEX_Match($m_Priority, '(?i)u')) != 0">
        <xsl:text>News - Need to know</xsl:text>
      </xsl:when>
      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(spot|obituary|game|topstory|headlinepackage)')) != 0 and
						    string-length(cp:REGEX_Match($m_Priority, '(?i)r')) != 0">
        <xsl:text>News - Good to know</xsl:text>
      </xsl:when>
      <!--File contenttype          : Enterprise or Feature	
          Priority Code             : anything (so dont need to check)
          Subject Classification    : Sports
          Then the file Ranking     : Feature - Premium-->
      <xsl:when
        test="string-length(cp:REGEX_Match($m_ContentType, '(?i)enterprise')) != 0 and
                      count(apcm:ContentMetadata/apcm:SubjectClassification[@Authority='AP Subject' and @Id='54df6c687df7100483dedf092526b43e']) > 0">
        <xsl:text>Feature - Premium</xsl:text>
      </xsl:when>
      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)enterprise')) != 0">
        <xsl:text>Feature - Regular</xsl:text>
      </xsl:when>
      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(review)')) != 0 and 
                      string-length(cp:REGEX_Match($m_SlugLine, '(?i)us-film-review')) != 0">
        <xsl:text>Feature - Regular</xsl:text>
      </xsl:when>
      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(column|profile|review)')) != 0">
        <xsl:text>Feature - Premium</xsl:text>
      </xsl:when>

      <!--News Digest downranking -->
      <xsl:when
        test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(Alaska-Digest-News|Washington-Digest|AP-Newsfeatures-Digest)')) != 0">
        <xsl:text>Routine</xsl:text>
      </xsl:when>
      <!--End News Digest downranking -->

      <xsl:when test="string-length(cp:REGEX_Match($m_ContentType, '(?i)(advisory|daybook)')) != 0">
        <xsl:text>Routine</xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:text>News - Optional</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>